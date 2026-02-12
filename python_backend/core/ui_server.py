"""
FRIDAY Omega — UI Server (WebSocket Bridge).
Bridges the Google Stitch UI to the Python backend (Multi-Agent System, STT, TTS).
"""
import sys
import os
import time
import logging
import base64
import threading
import tempfile

try:
    import imageio_ffmpeg
    os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
    print(f"[SYS] Injected embedded FFmpeg into PATH.")
except ImportError:
    pass

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLMEngine
from automation.humanoid_agent import HumanoidAgent
from automation.multi_agent_system import MultiAgentSystem
from core.stt import STTEngine
from core.tts import synthesize
from core.hardware_bridge import hardware_bridge
from core.blackboard import blackboard
import json

app = Flask(__name__)
# Enable CORS for the local HTML file explicitly
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ── INITIALIZE FRIDAY CORE ──
print("[UI Server] Initializing LLM Engine (DeepSeek-R1) and STT...")
llm = LLMEngine("deepseek-r1:8b") 
humanoid = HumanoidAgent(llm)
mas = MultiAgentSystem(llm, humanoid)
stt_engine = STTEngine(model_size="tiny.en")

# ── WEBSOCKET LOGGING HANDLER ──
# This intercepts logs and sends them to the UI terminal.
# It also detects tactical routing to light up the "Virtual Office" map.
class SocketIOLogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        
        # 1. Send to Terminal
        socketio.emit('terminal_log', {'text': log_entry})
        
        # 1.5 Send to Diagnostics Error Box
        if record.levelno >= logging.WARNING or "[Error" in log_entry or "Exception" in log_entry:
            socketio.emit('system_error', {'text': log_entry})
        
        # 2. Virtual Office Node Activation Tracker
        if "[Supervisor] Route ->" in log_entry:
            agent = log_entry.split("->")[1].strip()
            socketio.emit('node_active', {'node': agent, 'status': 'routing'})
        elif "Delegating to:" in log_entry: # Catch Director delegations
            agent = log_entry.split("Delegating to:")[1].strip()
            socketio.emit('node_active', {'node': agent, 'status': 'executing'})
        elif "[HardwareBridge] TRANSMIT ->" in log_entry:
            socketio.emit('node_active', {'node': 'hardware', 'status': 'transmitting'})

# Attach custom logger
ui_logger = logging.getLogger()
ui_logger.setLevel(logging.INFO)
ws_handler = SocketIOLogHandler()
ws_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S'))
ui_logger.addHandler(ws_handler)


def background_process(command: str):
    """Executes the MAS request in a separate thread to prevent WS blocking."""
    socketio.emit('status', {'state': 'thinking'})
    
    try:
        # Run MAS
        result = mas.process_request(command)
        
        # Send text result back to UI
        socketio.emit('final_result', {'text': result})
        
        # Generate Audio (TTS)
        socketio.emit('status', {'state': 'synthesizing_audio'})
        audio_bytes = synthesize(result, emotion="[NEUTRAL]", voice="am_adam")
        
        if audio_bytes:
            # Send base64 audio to UI speaker
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            socketio.emit('audio_response', {'data': f"data:audio/wav;base64,{audio_b64}"})
            
    except Exception as e:
        socketio.emit('terminal_log', {'text': f"ERROR: {e}"})
        
    socketio.emit('status', {'state': 'idle'})

@socketio.on('connect')
def test_connect():
    print("[UI Server] Frontend connected.")
    emit('status', {'state': 'connected'})
    # Trigger initial node status
    emit('node_active', {'node': 'CEO', 'status': 'idle'})

@socketio.on('process_command')
def handle_command(data):
    """Triggered when user types a text command."""
    command = data.get('command', '')
    print(f"[UI Server] Received text command: {command}")
    
    # Run in background to not block socket loop
    threading.Thread(target=background_process, args=(command,), daemon=True).start()

@socketio.on('process_audio')
def handle_audio(data):
    """Triggered when user finishes speaking into the UI mic."""
    socketio.emit('status', {'state': 'transcribing'})
    
    audio_b64 = data.get('audio', '')
    if not audio_b64:
        return
        
    try:
        # 1. Decode base64 WebM/WAV from browser
        audio_bytes = base64.b64decode(audio_b64.split(",")[1] if "," in audio_b64 else audio_b64)
        
        # 2. Write to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
            
        # 3. Transcribe via STT
        command_text = stt_engine.transcribe(temp_path)
        os.unlink(temp_path)
        
        if command_text:
            socketio.emit('transcription', {'text': command_text})
            # 4. Route back to MAS
            threading.Thread(target=background_process, args=(command_text,), daemon=True).start()
        else:
            socketio.emit('terminal_log', {'text': '[STT] No speech detected.'})
            socketio.emit('status', {'state': 'idle'})
            
    except Exception as e:
        socketio.emit('terminal_log', {'text': f"[STT Error] {e}"})
        socketio.emit('status', {'state': 'idle'})

@app.route('/')
def index():
    """Serves the Google Stitch HTML file (must be saved as friday_stitch_ui.html in app/)"""
    ui_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'app')
    return send_from_directory(ui_path, 'friday_stitch_ui.html')

def push_system_state():
    """Continuously pushes Hardware and Blackboard state to the UI."""
    import requests
    while True:
        try:
            # 0. Brain Health Ping
            try:
                res = requests.get("http://localhost:11434/", timeout=0.5)
                brain_status = "ONLINE" if res.status_code == 200 else "OFFLINE"
            except:
                brain_status = "OFFLINE"
            socketio.emit('brain_status', {'status': brain_status})

            # 1. Hardware Status
            hw_status = hardware_bridge.get_status()
            devices = []
            
            if hw_status.get("mode") == "simulator":
                devices.append({"name": "SIMULATOR_MODE", "icon": "dns", "status": "VIRTUAL"})
            else:
                for dev_id, info in hw_status.get("devices", {}).items():
                    icon = "memory" if "flipper" in info.get("type", "") else "router"
                    devices.append({"name": str(dev_id).upper(), "icon": icon, "status": "ONLINE"})
                    
            if not devices:
                devices.append({"name": "NO_HARDWARE", "icon": "cloud_off", "status": "OFFLINE"})
                
            socketio.emit('update_hardware', {'devices': devices})

            # 2. Blackboard State
            bb_state = blackboard.export_state()
            state_dict = json.loads(bb_state)
            intel_html = ""
            for target, data in state_dict.items():
                intel_html += f"<b>TARGET: {target}</b><br>"
                if data.get("vulns"): intel_html += f"Vulns: {len(data['vulns'])} detected<br>"
                if data.get("ports"): intel_html += f"Ports: {len(data['ports'])} open<br>"
                if data.get("creds"): intel_html += f"Creds: {len(data['creds'])} found<br>"
                intel_html += "<hr class='border-outline-variant/30 my-1'>"
            
            if not intel_html:
                intel_html = "AWAITING INTELLIGENCE..."
                
            socketio.emit('update_blackboard', {'text': intel_html})
            
        except Exception as e:
            logging.error(f"State Push Error: {e}")
            
        time.sleep(2)

# Start background sync
threading.Thread(target=push_system_state, daemon=True).start()

if __name__ == '__main__':
    print(f"[UI Server] Starting WebSocket API on port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
