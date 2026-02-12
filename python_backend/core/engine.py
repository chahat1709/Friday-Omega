import asyncio
import numpy as np
import time
import re
import requests
from .vad import VADEngine
from .stt import STTEngine
from .llm import LLMEngine
from .tts import TTSEngine
from .tools import Tools
# Import HumanoidAgent and MultiAgentSystem from sibling package 'automation'
try:
    from ..automation.humanoid_agent import HumanoidAgent
    from ..automation.multi_agent_system import MultiAgentSystem
    from .plan_validator import PlanValidator
    from .failsafe import failsafe
except (ImportError, ValueError):
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from automation.humanoid_agent import HumanoidAgent
    from automation.multi_agent_system import MultiAgentSystem
    from core.plan_validator import PlanValidator
    from core.failsafe import failsafe


# SECURITY CONFIGURATION
# Set to True ONLY on the developer's machine.
# This enables the AI to modify its own source code.
DEVELOPER_MODE = False  # Set True ONLY for development

class VoiceEngine:
    def __init__(self):
        print("DEBUG: Init VAD")
        self.vad = VADEngine()
        # STT will auto-select best device/model (small on GPU if available)
        print("DEBUG: Init STT")
        self.stt = STTEngine() 
        # LLM: Switched to local llama3.1:8b since deepseek is not downloaded
        print("DEBUG: Init LLM (llama3.1)")
        self.llm = LLMEngine("llama3.1:8b", n_ctx=8192) 
        print("DEBUG: Init TTS")
        self.tts = TTSEngine()
        print("DEBUG: Init HumanoidAgent")
        self.humanoid = HumanoidAgent(self.llm)
        self.agent = self.humanoid # Backward compatibility alias
        
        # Multi-Agent Cyber System (11 agents: pentest, OSINT, workflow, etc.)
        print("DEBUG: Init MultiAgentSystem")
        try:
            self.cyber_agents = MultiAgentSystem(self.llm, self.humanoid)
        except Exception as e:
            print(f"DEBUG: MultiAgentSystem Init Failed: {e}. Security features disabled.")
            self.cyber_agents = None
        
        # Strategic Command Layer
        print("DEBUG: Init PlanValidator (Maker-Checker)")
        self.validator = PlanValidator(self.llm)
        self.failsafe = failsafe
        
        self.audio_buffer = []
        self.is_speaking = False
        self.silence_start = None
        self.interrupted = False
        self.latest_image = None # Store latest frame for vision
        
        # Memory / Adaptive Engine
        print("DEBUG: Init Memory")
        try:
            from .adaptive_engine import AdaptiveEngine
            self.memory = AdaptiveEngine()
        except Exception as e:
            print(f"DEBUG: Memory Init Failed: {e}. Using Mock Memory.")
            class MockAdaptiveEngine:
                def remember_interaction(self, *args, **kwargs): pass
                def recall_context(self, *args, **kwargs): return ""
                def process_feedback(self, *args, **kwargs): pass
            self.memory = MockAdaptiveEngine()
        
        print("DEBUG: Engine Init Complete")

        self.turn_task = None
        self.history = [] # Conversation History

    async def process_audio_stream(self, websocket):
        """
        Main loop: Receive audio -> VAD -> STT -> LLM -> TTS -> Send Audio
        """
        print("Voice Engine Started (Duplex Mode)")
        
        try:
            while True:
                try:
                    message = await websocket.receive()
                except RuntimeError:
                    # WebSocket disconnected
                    break
                except Exception as e:
                    print(f"WS Receive Error: {e}")
                    break
                
                # Debug: Print message type if not bytes (too spanmy)
                # if 'bytes' not in message: print(f"WS Msg: {message.keys()}")

                try:
                    # Handle JSON messages (e.g. video frames)
                    if message.get('type') == 'websocket.receive' and 'text' in message:
                        try:
                            import json
                            data = json.loads(message['text'])
                            if data.get('type') == 'video_frame' and 'image' in data:
                                self.latest_image = data['image'] # Base64 string
                            elif data.get('type') == 'event' and data.get('action') == 'greet':
                                print("Received Greeting Trigger")
                                # Cancel previous turn if any
                                if self.turn_task and not self.turn_task.done():
                                    self.turn_task.cancel()
                                self.turn_task = asyncio.create_task(self.greet(websocket))
                        except Exception as e:
                            print(f"JSON Error: {e}")
                        continue

                    # Assume message is bytes (audio chunk)
                    if message.get('type') == 'websocket.receive' and 'bytes' in message:
                        audio_bytes = message['bytes']
                        
                        # Validate length
                        if len(audio_bytes) < 100: continue

                        # Convert bytes to float32 numpy array for VAD
                        # Assuming 16khz mono 16-bit int input
                        audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
                        audio_float32 = audio_int16.astype(np.float32) / 32768.0
                        
                        # VAD Check
                        is_speech = self.vad.is_speech(audio_float32)
                        
                        if is_speech:
                            if not self.is_speaking:
                                print("User started speaking (Interruption Triggered)")
                                self.is_speaking = True
                                self.interrupted = True # Signal to stop any current TTS
                                
                                # Cancel any running AI turn immediately
                                if self.turn_task and not self.turn_task.done():
                                    self.turn_task.cancel()
                                    
                                self.audio_buffer = [] # Clear buffer for new utterance
                            
                            self.audio_buffer.append(audio_int16)
                            self.silence_start = None
                        else:
                            if self.is_speaking:
                                if self.silence_start is None:
                                    self.silence_start = time.time()
                                
                                # Silence > 0.4s? Commit. (Faster response)
                                if time.time() - self.silence_start > 0.4:
                                    print(f"Silence detected ({len(self.audio_buffer)} chunks), processing...")
                                    self.is_speaking = False
                                    self.interrupted = False
                                    
                                    # Launch Turn in Background (Non-Blocking)
                                    if self.turn_task and not self.turn_task.done():
                                        self.turn_task.cancel()
                                    self.turn_task = asyncio.create_task(self.handle_turn(websocket, list(self.audio_buffer)))
                                    
                                    self.audio_buffer = []
                                    self.vad.reset()
                                    
                                    # Bug #12 fix: Trim voice history to prevent RAM exhaustion
                                    if len(self.history) > 20:
                                        self.history = self.history[-20:]

                except Exception as inner_e:
                    print(f"Processing Error (Ignored): {inner_e}")
                    continue

        except Exception as e:
            print(f"Stream Error: {e}")

    async def greet(self, websocket):
        # Generate Jarvis-style greeting
        hour = time.localtime().tm_hour
        greeting = "Good evening" if hour >= 18 else "Good afternoon" if hour >= 12 else "Good morning"
        
        # Short, crisp, robotic but polite
        text = f"{greeting} Sir. Systems are online."
        print(f"Greeting: {text}")
        
        # Synthesize
        audio_bytes = self.tts.synthesize(text, "[NEUTRAL]")
        if audio_bytes:
             try: await websocket.send_bytes(audio_bytes)
             except Exception as ws_err:
                 print(f"[Greeting] WebSocket send failed: {ws_err}")
                 return  # Stop processing for dead connection
        
        await websocket.send_json({"type": "status", "state": "listening"})

    async def handle_turn(self, websocket, audio_buffer):
        # 1. STT
        full_audio = np.concatenate(audio_buffer)
        # Normalize to float32 for Whisper if needed, or pass int16 if supported
        # faster-whisper usually takes float32
        full_audio_float = full_audio.astype(np.float32) / 32768.0
        
        text = self.stt.transcribe(full_audio_float)
        print(f"User: {text}")
        
        if not text.strip():
            return

        # 1.5 Fast Intent Router (Latency Optimization)
        fast_response = self.check_fast_intent(text)
        if fast_response:
            print(f"Fast Intent Triggered: {fast_response}")
            full_response = fast_response
            # Skip LLM
        else:
            # 2. LLM via Local Engine (Bypassing external brain for reliability)
            try:
                # Check for Visual Intent (STRICT: only screen/camera Commands, not general questions)
                vision_keywords = ["look at", "see this", "show me", "screen", "camera", "holding", "hand"]
                is_visual = any(keyword in text.lower() for keyword in vision_keywords)
                
                if is_visual and self.latest_image:
                    print("Visual Intent Detected")
                    # Use LLaVA via Ollama (fallback for now as loading CLIP in-memory is heavy)
                    try:
                        full_response = self.llm.generate_with_image(
                            system_prompt="You are F.R.I.D.A.Y.'s Vision System. Describe the image concisely.",
                            user_prompt=text,
                            image_base64=self.latest_image
                        )
                        if "Error" in full_response or "Connection" in full_response:
                             raise Exception(full_response)
                    except Exception as e:
                         print(f"Vision Error: {e}")
                         full_response = "[NEUTRAL] My vision system is currently offline. Please ensure Ollama is running safely."
                         # Optional: Auto-start logic could go here, but risky for stability.
                else:
                    # Standard Text Chat
                    # Async LLM generation to prevent blocking WebSocket heartbeat
                    full_response = await asyncio.to_thread(self.llm.generate, text)
                    
                print(f"LLM Response: {full_response[:50]}...")
            
            except Exception as e:
                print(f"Local LLM Error: {e}")
                # DEGRADED MODE: Failsafe Fallback
                fallback = self.failsafe.get_fallback_action(text)
                full_response = fallback["instruction"]
                if fallback["intent"] != "CHAT":
                    full_response = f"[CMD: cyber_agent \"{text}\"] Switching to DEGRADED MODE. {fallback['instruction']}"

        # Parse response for streaming
        current_sentence = ""
        emotion = "[NEUTRAL]"
        
        # Send "Thinking" status
        await websocket.send_json({"type": "status", "state": "thinking"})

        for token in full_response.split():  # Simple tokenization
            if self.interrupted:
                break
            
            current_sentence += token + " "
            
            # Check for emotion tag
            if token.startswith("[") and "]" in token and "CMD" not in token:
                emotion = token
                continue
                
            # Check for sentence end
            if re.search(r'[.!?]\s*$', current_sentence) and "[CMD:" not in current_sentence:
                clean_sentence = re.sub(r'\[CMD:.*?\]', '', current_sentence).strip()
                if clean_sentence:
                    print(f"Synthesizing: {clean_sentence} ({emotion})")
                    audio_bytes = self.tts.synthesize(clean_sentence, emotion)
                    
                    if self.interrupted:
                        break
                        
                    # Send Audio
                    await websocket.send_bytes(audio_bytes)
                current_sentence = ""
        
        # Flush remaining
        if current_sentence and not self.interrupted:
             clean_sentence = re.sub(r'\[CMD:.*?\]', '', current_sentence).strip()
             if clean_sentence:
                 audio_bytes = self.tts.synthesize(clean_sentence, emotion)
                 await websocket.send_bytes(audio_bytes)

        # 3. Execute Commands
        cmd_matches = re.findall(r'\[CMD:\s*(.*?)\]', full_response)
        execution_results = self.execute_commands(cmd_matches)

        # If there are execution results, synthesize them
        if execution_results:
            results_text = " ".join(execution_results)
            print(f"Synthesizing execution results: {results_text}")
            audio_bytes = self.tts.synthesize(results_text, "[NEUTRAL]")
            if audio_bytes:
                await websocket.send_bytes(audio_bytes)

        await websocket.send_json({"type": "status", "state": "listening"})

    def process_text_command(self, text):
        """Unified pipeline for Text Chat to match Voice capabilities"""
        print(f"Processing Text Command: {text}")
        
        # Fast Intent
        fast_response = self.check_fast_intent(text)
        if fast_response:
            full_response = fast_response
            # Add to history even if fast intent? Maybe.
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "assistant", "content": full_response})
        else:
            try:
                # Check Visual (STRICT: only screen/camera commands, not general questions)
                vision_keywords = ["look at", "see this", "show me", "screen", "camera", "holding", "hand"]
                is_visual = any(keyword in text.lower() for keyword in vision_keywords)
                if is_visual and self.latest_image:
                     full_response = self.llm.generate_with_image("Describe image.", text, self.latest_image)
                else:
                     # Pass History (using keyword arg to avoid positional mismatch)
                     full_response = self.llm.generate(text, history=self.history)
                
                # Update History
                self.history.append({"role": "user", "content": text})
                self.history.append({"role": "assistant", "content": full_response})
                
                # Keep history manageable (last 10 turns)
                if len(self.history) > 20:
                    self.history = self.history[-20:]
                    
            except Exception as e:
                print(f"Text Process Error: {e}")
                # DEGRADED MODE: Failsafe Fallback
                fallback = self.failsafe.get_fallback_action(text)
                full_response = fallback["instruction"]
                if fallback["intent"] != "CHAT":
                    full_response = f"[CMD: cyber_agent \"{text}\"] [DEGRADED MODE] {fallback['instruction']}"
                return full_response

        cmd_matches = re.findall(r'\[CMD:\s*(.*?)\]', full_response)
        results = self.execute_commands(cmd_matches)
        if results:
             full_response += "\n\n[Action Results]: " + " ".join(results)
             # Update the assistant message in history to include results? 
             # For now, let's just leave the reasoning in history.
             
        return full_response

    def execute_commands(self, cmd_matches):
        results = []
        for cmd_str in cmd_matches:
            print(f"Executing Command: {cmd_str}")
            try:
                if "open_app" in cmd_str: results.append(Tools.open_app(cmd_str.split('"')[1]))
                elif "play_music" in cmd_str:
                     if '"' in cmd_str: results.append(Tools.play_music(cmd_str.split('"')[1]))
                     else: results.append(Tools.play_music())
                elif "play_youtube" in cmd_str: results.append(Tools.play_youtube(cmd_str.split('"')[1]))
                elif "stop_music" in cmd_str: results.append(Tools.stop_music())
                elif "next_song" in cmd_str: results.append(Tools.next_song())
                elif "previous_song" in cmd_str: results.append(Tools.previous_song())
                elif "get_location" in cmd_str: results.append(Tools.get_location())
                elif "send_whatsapp" in cmd_str:
                     args = re.findall(r'"(.*?)"', cmd_str)
                     if len(args) >= 2: results.append(Tools.send_whatsapp(args[0], args[1]))
                elif "god_mode" in cmd_str:
                     try:
                        instruction = cmd_str.split('"')[1]
                        print(f"GOD MODE: {instruction}")
                        if self.humanoid: 
                             # 3.1 HRM Heuristic: Long commands -> Plan
                             if len(instruction.split()) > 6:
                                 res = self.humanoid.plan_mission(instruction)
                             else:
                                 res = self.humanoid.solve_task(instruction)
                             results.append(f"God Mode Result: {res}")
                        else:
                             results.append("Humanoid Agent not initialized.")
                     except IndexError:
                        results.append("God Mode Error: No instruction provided.")
                elif "improve_code" in cmd_str:
                        if not DEVELOPER_MODE:
                            results.append("Access Denied: Code modification is restricted to Developer Mode.")
                            continue

                        args = re.findall(r'"(.*?)"', cmd_str)
                        if len(args) >= 2:
                            filename = args[0]
                            instruction = args[1]
                            
                            # 1. Read File
                            code_content = Tools.read_file_content(filename)
                            if "Error" in code_content or "Access denied" in code_content:
                                results.append(f"Failed to read {filename}: {code_content}")
                            else:
                                # 2. Generate New Code (works in BOTH Ollama and GGUF modes)
                                code_prompt = f"You are an expert Python developer. Modify the file '{filename}' based on this instruction: {instruction}\n\nCurrent Code:\n```python\n{code_content}\n```\n\nReturn ONLY the full updated code, no explanations."
                                
                                print(f"Generating code improvement for {filename}...")
                                try:
                                    generated_text = self.llm.generate(
                                        prompt=code_prompt,
                                        system_prompt="You are an expert Python developer. Return ONLY code, no explanations.",
                                        temperature=0.1
                                    )
                                
                                    # Clean up if LLM added markdown
                                    if generated_text.startswith("```python"): generated_text = generated_text[9:]
                                    elif generated_text.startswith("```"): generated_text = generated_text[3:]
                                    if generated_text.endswith("```"): generated_text = generated_text[:-3]
                                    
                                    # 3. Write File
                                    write_result = Tools.write_file_content(filename, generated_text.strip())
                                    results.append(f"Code Update: {write_result}. Please restart the backend to apply changes.")
                                except Exception as llm_err:
                                    results.append(f"Code generation failed: {llm_err}")

                elif "cyber_agent" in cmd_str:
                    try:
                        instruction = cmd_str.split('"')[1]
                        print(f"CYBER AGENT: {instruction}")
                        if self.cyber_agents:
                            res = self.cyber_agents.process_request(instruction)
                            results.append(f"Security Agent Result: {res}")
                        else:
                            results.append("Security agent system not initialized. Check backend logs.")
                    except IndexError:
                        results.append("Cyber Agent Error: No instruction provided.")
                elif "set_volume" in cmd_str:
                     level = re.search(r'\d+', cmd_str)
                     if level: results.append(Tools.set_volume(int(level.group())))
                elif "volume_up" in cmd_str: results.append(Tools.volume_up())
                elif "volume_down" in cmd_str: results.append(Tools.volume_down())
                elif "set_brightness" in cmd_str:
                     level = re.search(r'\d+', cmd_str)
                     if level: results.append(Tools.set_brightness(int(level.group())))
            except Exception as e:
                print(f"Cmd Error: {e}")
                results.append(f"Error executing {cmd_str}: {e}")
        return results

    def check_fast_intent(self, text):
        """
        Bypasses LLM for common, simple commands to reduce latency from 50s to 0.1s.
        Returns formatted response string with [CMD] tag if matched, else None.
        """
        text_lower = text.lower().strip()
        
        # 1. Music
        # Matches: "play saiyara", "play some music", "play song x"
        match = re.search(r'^play\s+(.+)', text_lower)
        if match:
            song = match.group(1).replace('song', '').replace('music', '').strip()
            return f"[CMD: play_music \"{song}\"] Playing {song}."

        # 2. Volume
        # Matches: "set volume to 50", "volume 50", "turn volume to 20"
        match = re.search(r'volume\s+(?:to\s+)?(\d+)', text_lower)
        if match:
            level = match.group(1)
            return f"[CMD: set_volume \"{level}\"] Setting volume to {level}%."

        # 2.5 Brightness
        # Matches: "set brightness to 50", "brightness 50"
        match = re.search(r'brightness\s+(?:to\s+)?(\d+)', text_lower)
        if match:
            level = match.group(1)
            return f"[CMD: set_brightness \"{level}\"] Setting brightness to {level}%."
        
        # 3. App Control (Simple Only)
        # Matches: "open notepad", "launch chrome"
        # STRICT REGEX: Prevents capturing complex commands like "Open notepad and type..."
        match = re.search(r'^(open|launch|start)\s+([a-zA-Z0-9\s]+?)$', text_lower)
        if match:
            app = match.group(2).strip()
            # If app name is too long (implies complex instruction), skip Fast Intent
            if len(app.split()) <= 4:
                return f"[CMD: open_app \"{app}\"] Opening {app}."
            # Else fall through to LLM -> God Mode

        # 4. Stop
        if "stop music" in text_lower or "stop playing" in text_lower:
            return "[CMD: stop_music] Stopping music."
        
        # 5. God Mode Keywords (Humanoid)
        # If user explicitly says "type", "click", "scroll" -> God Mode
        # Also "Look at the screen" -> God Mode (to leverage Humanoid Vision)
        if any(v in text_lower for v in ["click", "type", "scroll", "press"]) or "screen" in text_lower:
             return f"[CMD: god_mode \"{text}\"] Executing interface action."

        # 6. Cyber Security Keywords -> MultiAgentSystem
        security_keywords = [
            "scan", "nmap", "pentest", "penetration", "vulnerability", "exploit",
            "osint", "recon", "reconnaissance", "whois", "shodan", "cve",
            "audit", "bug hunt", "nikto", "gobuster", "sqlmap", "hydra",
            "network scan", "port scan", "wifi", "iot", "arp",
            "adb", "android", "mobile audit", "workflow", "full audit",
            "metasploit", "virustotal", "dns recon", "web scan"
        ]
        if any(kw in text_lower for kw in security_keywords):
            return f"[CMD: cyber_agent \"{text}\"] Routing to security agent system."

        return None
