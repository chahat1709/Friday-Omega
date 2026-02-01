import uvicorn
from fastapi import FastAPI, WebSocket, File, UploadFile, Request
from core.engine import VoiceEngine
from modules.router import Router
from modules.action_engine import ActionEngine
import os
import sys
import threading
import asyncio
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"], # Restrict to known frontends
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Security Configuration
API_KEY = os.getenv("FRIDAY_API_KEY", "friday_omega_dev_key") # Default for dev, override in .env

async def verify_api_key(request: Request):
    if request.url.path in ["/status", "/health", "/api/system/status"]:
        return # Public endpoints
        
    auth_key = request.headers.get("X-API-Key")
    if not auth_key or auth_key != API_KEY:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid or missing API Key")
# Lazy engine initialization to keep server responsive while heavy models load
engine = None
engine_lock = threading.Lock()
engine_ready_event = threading.Event()

def _init_engine_background():
    global engine
    try:
        print("[Engine] Initializing VoiceEngine in background thread...")
        engine = VoiceEngine()
        print("[Engine] VoiceEngine initialization complete.")
        engine_ready_event.set()
    except Exception as e:
        print(f"[Engine] Failed to initialize VoiceEngine: {e}")

def ensure_engine_initialized(nonblocking=False, timeout=None):
    """Ensure the global engine is being initialized.
    If nonblocking=True, returns immediately after triggering init.
    If nonblocking=False, waits until initialization completes or timeout expires.
    """
    global engine
    with engine_lock:
        if engine is None and not engine_ready_event.is_set():
            # Start background initialization thread
            t = threading.Thread(target=_init_engine_background, daemon=True)
            t.start()

    if nonblocking:
        return False

    # Wait for engine to be ready
    waited = engine_ready_event.wait(timeout=timeout)
    return waited

# Agent modules
router = Router()
action_engine = ActionEngine()

# Trigger background initialization on startup (non-blocking)
ensure_engine_initialized(nonblocking=True)

@app.websocket("/ws/audio")
async def audio_websocket(websocket: WebSocket):
    await websocket.accept()
    # Notify client of engine status and wait until ready
    try:
        if not engine_ready_event.is_set():
            await websocket.send_json({"type": "status", "status": "loading"})
            # wait but remain responsive (max 120s)
            await asyncio.get_event_loop().run_in_executor(None, engine_ready_event.wait, 120)

        if not engine_ready_event.is_set():
            # Still not ready
            await websocket.send_json({"type": "status", "status": "not_ready"})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "status": "ready"})
        await engine.process_audio_stream(websocket)
    except Exception as e:
        print(f"[WS] audio_websocket error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass

@app.post("/stt")
async def stt(request: Request):
    await verify_api_key(request)
    import tempfile
    
    audio_data = await request.body()
    
    # Save to temp file to handle various formats (WebM, WAV, etc.) via ffmpeg/av in faster-whisper
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name
    
    # Ensure engine is initialized (wait a short time)
    ready = ensure_engine_initialized(nonblocking=False, timeout=30)
    if not ready:
        # If engine is not ready within timeout, return informative error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {"success": False, "error": "engine_loading"}

    try:
        text = engine.stt.transcribe(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
            
    return {"success": True, "text": text}

@app.post("/llm")
async def llm(request: dict, req: Request):
    await verify_api_key(req)
    prompt = request.get("prompt", "")
    history = request.get("history", [])
    
    # 1. Recall Context (RAG)
    context = ""
    try:
        context = engine.memory.recall_context(prompt)
    except Exception as e:
        print(f"[Memory] Recall failed: {e}")

    # 2. Augment Prompt with Context
    if context:
        # We perform a 'soft' injection by prepending to the user prompt or handling it in llm.generate
        # For now, let's prepend to the prompt so the LLM sees it.
        # But `llm.generate` builds the chat history.
        # Let's pass it cleanly.
        full_wrapper_prompt = f"Context from past memory:\n{context}\n\nUser Query: {prompt}"
    else:
        full_wrapper_prompt = prompt

    response = engine.llm.generate(full_wrapper_prompt, history)
    
    # 3. Remember Interaction (Background)
    # We want to remember the ORIGINAL prompt, not the augmented one
    try:
        engine.memory.remember_interaction(prompt, response)
    except Exception as e:
        print(f"[Memory] Remember failed: {e}")

    return {"success": True, "response": response}

@app.post("/upload_frame")
async def upload_frame(req: Request):
    await verify_api_key(req)
    try:
        data = await req.json()
        # Expecting { "frameData": "data:image/jpeg;base64,..." }
        frame_data = data.get("frameData")
        if frame_data:
            # Check if it has the prefix, if so, strip it so we have raw base64 for some models, 
            # OR keep it if that's what generate_with_image expects.
            # LLaVA (Ollama) typically expects raw base64 in the 'images' array (no prefix).
            if "," in frame_data:
                frame_data = frame_data.split(",")[1]
            
            engine.latest_image = frame_data
            return {"success": True}
        return {"success": False, "error": "No frame data"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tts")
async def tts_endpoint(request: dict, req: Request):
    await verify_api_key(req)
    from fastapi.responses import Response
    text = request.get("text", "")
    emotion = request.get("emotion", "[NEUTRAL]")
    
    if not ensure_engine_initialized(nonblocking=False, timeout=30):
        return {"success": False, "error": "Engine loading"}

    audio_bytes = engine.tts.synthesize(text, emotion)
    
    if not audio_bytes:
         return {"success": False, "error": "TTS generation failed"}
         
    return Response(content=audio_bytes, media_type="audio/wav")


@app.get("/status")
async def status():
    return {"ready": engine_ready_event.is_set(), "loading": not engine_ready_event.is_set()}


@app.post("/command")
async def command_route(req: Request):
    await verify_api_key(req)
    data = await req.json()
    text = data.get('text', '')

    # Unified Routing (All text goes through the Brain now)
    try:
        response = engine.process_text_command(text)
        return {"intent": "CHAT", "result": response}
    except Exception as e:
        return {"intent": "CHAT", "result": f"Error: {e}"}

@app.post("/api/voice/process")
async def process_voice_file(audio: UploadFile = File(...)):
    """Handles offline voice processing (wav file -> transcript)"""
    print(f"Received Voice File: {audio.filename}")
    try:
        if not engine:
            return {"success": False, "error": "engine_loading"}
        
        # Save to temp
        temp_filename = f"temp_voice_{int(time.time())}_{audio.filename}"
        with open(temp_filename, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
            
        # Transcribe
        print("Transcribing...")
        # Run in thread pool to avoid blocking async loop
        transcript = await asyncio.to_thread(engine.stt.transcribe, temp_filename)
        print(f"Server STT Transcript: {transcript}")
        
        # Cleanup
        try: os.remove(temp_filename)
        except: pass
        
        return {"success": True, "transcript": transcript}
    except Exception as e:
        print(f"Voice Process Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/voice-command")
async def voice_command_endpoint(request: Request):
    """Handles voice command execution (transcript -> action)"""
    try:
        data = await request.json()
        transcript = data.get("transcript")
        if not transcript:
            return {"success": False, "error": "No transcript provided"}
            
        if not engine:
            return {"success": False, "error": "Engine not ready"}

        print(f"Executing Voice Command: {transcript}")
        # Process command
        response_text = await asyncio.to_thread(engine.process_text_command, transcript)
        
        return {
            "success": True,
            "message": response_text,
            "response": response_text
        }
    except Exception as e:
        print(f"Voice Command Error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/metrics")
async def metrics():
    import psutil
    return {
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "network": 0, # Placeholder
        "temp": 0 # Placeholder
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/system/status")
async def system_status_api():
    return {"ready": engine_ready_event.is_set(), "loading": not engine_ready_event.is_set()}

@app.get("/api/ollama/status")
async def ollama_status():
    import requests
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=1)
        if res.status_code == 200:
            return {"status": "online", "model": "llama3"}
    except:
        pass
    return {"status": "offline"}

@app.post("/api/camera/init")
async def camera_init():
    if not engine: return {"success": False, "error": "Engine loading"}
    # Use existing Vision module if available
    # For now, just return success since frontend handles webcam mostly?
    # Actually frontend does getUserMedia.
    # So this endpoint might be for SERVER-SIDE camera (e.g. OpenCV).
    # Since Humanoid uses Screen+Webcam, let's just acknowledge.
    return {"success": True, "message": "Server Camera Helper Ready"}

@app.post("/api/camera/stop")
async def camera_stop():
    return {"success": True}

if __name__ == "__main__":
    # Hardware Check
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Starting Voice Server on {device.upper()}...")
    
    # DYNAMIC PORT HANDSHAKE (Smart Framework)
    # 1. Find a free port automatically
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('0.0.0.0', 0)) # Bind to port 0 (OS picks free port)
    port = sock.getsockname()[1]
    sock.close()

    print(f"SMART FRAMEWORK: Binding to Dynamic Port {port}")

    # 2. Write the port to a config file for the Frontend to read
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.js")
    with open(config_path, "w") as f:
        f.write(f"const RUNTIME_PORT = {port};\n")
        f.write(f"const API_BASE_DYNAMIC = 'http://localhost:{port}';\n")
    
    print(f"HANDSHAKE: Config written to {config_path}")

    # 3. Start Server on that port
    uvicorn.run(app, host="0.0.0.0", port=port)
