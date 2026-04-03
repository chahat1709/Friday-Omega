import os
import sys
import json
from dotenv import load_dotenv
import re
from memory_engine import MemoryEngine
from persona_manager import PersonaManager
from hands import Hands

# Load environment variables
load_dotenv()

class FridayBrain:
    def __init__(self, user_name="Jain"):
        self.memory = MemoryEngine()
        self.persona = PersonaManager(user_name=user_name)
        self.hands = Hands()
        self.model = None  # Offline only, no cloud models

        # Attempt to create a local LLM
        self.local_llm = None
        
        # **OFFLINE MODE** - Check for explicit GGUF model path first (no auto-download)
        gguf_model_path = os.getenv('GPT4ALL_MODEL_PATH')
        if gguf_model_path and os.path.exists(gguf_model_path):
            try:
                from ctransformers import AutoModelForCausalLM
                self.local_llm = AutoModelForCausalLM.from_pretrained(
                    model_path_or_repo_id=gguf_model_path,
                    model_type="mistral",
                    gpu_layers=50,  # Use GPU if available
                    verbose=False
                )
                print(f"[Brain] ✓ OFFLINE MODE: Using GGUF model from {gguf_model_path}", file=sys.stderr)
                print(f"[Brain] ✓ No internet required - this instance is 100% offline", file=sys.stderr)
                print(f"[Brain] ✓ All operations are completely local - will work without internet", file=sys.stderr)
            except Exception as e:
                self.local_llm = None
                print(f"[Brain] WARNING: GGUF model load failed: {e}", file=sys.stderr)
        
        # **FALLBACK** - Try GPT4All but ONLY if pre-downloaded (no auto-download)
        if not self.local_llm:
            try:
                from gpt4all import GPT4All
                model_name = os.getenv('GPT4ALL_MODEL', 'gpt4all-lora-quantized')
                # IMPORTANT: Only attempt if environment explicitly sets NO_AUTO_DOWNLOAD
                # or if model already cached in ~/.cache/gpt4all/
                if os.getenv('GPT4ALL_NO_AUTO_DOWNLOAD') == '1':
                    self.local_llm = GPT4All(
                        model_name=model_name,
                        allow_download=False  # CRITICAL: Disable auto-downloads in offline mode
                    )
                    print(f"[Brain] Using cached GPT4All model: {model_name}", file=sys.stderr)
                else:
                    # In default mode, still try but be prepared for failure
                    try:
                        self.local_llm = GPT4All(model_name=model_name)
                        print(f"[Brain] Using GPT4All model: {model_name}", file=sys.stderr)
                    except Exception as e:
                        self.local_llm = None
                        print(f"[Brain] GPT4All not available: {e}", file=sys.stderr)
            except Exception as e:
                self.local_llm = None
                print(f"[Brain] Local LLM not available: {e}", file=sys.stderr)

    def think(self, user_input, image_path=None, screen_path=None):
        print("[Brain] Offline mode: Using local LLM only", file=sys.stderr)
        # 1. Determine Persona
        mode = self.persona.detect_mode(user_input)
        
        # 2. Check Memory for Triggers & User Profile
        temporal_context = self.memory.check_temporal_triggers()
        user_profile = self.memory.get_user_profile()
        
        # 3. Build System Prompt
        # Inject user profile into the context
        full_context = f"{temporal_context}\n\n{user_profile}"
        system_instruction = self.persona.get_system_instruction(full_context)
        
        # 4. Get Conversation History
        history = self.memory.get_recent_context(limit=5)
        
        # 5. Construct Chat Session
        # We'll construct a simple prompt for now
        full_prompt = [f"SYSTEM: {system_instruction}\n\n"]
        for msg in history:
            full_prompt.append(f"{msg['role'].upper()}: {msg['content']}\n")
        full_prompt.append(f"USER: {user_input}\nMODEL:")
        
        # Flatten prompt for text-only, or keep list for multimodal
        generation_input = []
        text_prompt = "".join(full_prompt)
        
        images_to_process = []
        
        # Process Webcam Image
        if image_path:
            print(f"[Brain] Received webcam image: {image_path}", file=sys.stderr)
            try:
                import PIL.Image
                img = PIL.Image.open(image_path)
                images_to_process.append(img)
                text_prompt += """
[SYSTEM: VISUAL ANALYSIS (WEBCAM).
Image 1 is from the user's webcam. Analyze their face, clothing, and immediate surroundings.
1. SCAN for: Identity, Clothing, Accessories (glasses, hats, etc.), Action, Mood.
2. IF asked "Can you see me?" or "What am I wearing?", describe this image.
3. Log observation as [VISUAL_LOG: ...]
]
"""
            except Exception as e:
                text_prompt += f"\n[System Error: Could not load webcam image: {e}]"
        else:
            text_prompt += """
[SYSTEM: NO WEBCAM IMAGE.
The user has NOT provided a webcam image.
1. IF the user asks "Can you see me?", "What am I wearing?", or "Did I wear glasses?", you MUST reply: "I cannot see you right now. Please ensure your camera is active."
2. Do NOT hallucinate or guess what the user looks like.
]
"""

        # Process Screen Capture
        if screen_path:
            print(f"[Brain] Received screen capture: {screen_path}")
            try:
                import PIL.Image
                screen_img = PIL.Image.open(screen_path)
                images_to_process.append(screen_img)
                text_prompt += """
[SYSTEM: DESKTOP ANALYSIS (SCREENSHOT).
Image 2 (or the last image) is a screenshot of the user's desktop.
1. SCAN for: Open applications, text content, websites, code, or media.
2. IF asked "What am I doing?" or "What's on my screen?", describe this image.
3. Combine this with webcam context to understand the user's full activity (e.g., "You are coding in VS Code while drinking coffee").
]
"""
            except Exception as e:
                text_prompt += f"\n[System Error: Could not load screen capture: {e}]"

        generation_input.append(text_prompt)
        generation_input.extend(images_to_process)
        
        reply = ""
        action_result = ""
        
        try:
            # Offline only: Use local LLM
            if self.local_llm:
                prompt_text = text_prompt
                try:
                    # Support both ctransformers and GPT4All APIs
                    if hasattr(self.local_llm, '__call__'):  # ctransformers style
                        reply = self.local_llm(prompt_text, max_new_tokens=256)
                    else:  # GPT4All style
                        response = self.local_llm.generate(prompt_text)
                        reply = response if isinstance(response, str) else getattr(response, 'text', str(response))
                except Exception as generr:
                    print(f"[Brain] Local LLM generation failed: {generr}", file=sys.stderr)
                    reply = "I'm here, but my local LLM failed to respond."
            else:
                reply = "Offline mode: No local LLM available. Please ensure Ollama or a local model is running."

            # Parse Visual Logs (runs on ANY reply)
            visual_logs = re.findall(r'\[VISUAL_LOG: (.*?)\]', reply)
            for log in visual_logs:
                self.memory.log_visual_observation(log)
                print(f"[Brain] Visual Log: {log}", file=sys.stderr)
                # Remove log from spoken reply
                reply = reply.replace(f"[VISUAL_LOG: {log}]", "")

            # Parse Actions
            # Regex to capture [ACTION: name] or [ACTION: name: value]
            actions = re.findall(r'\[ACTION: ([\w_]+)(?::\s*(.*?))?\]', reply)
            for action, value in actions:
                # Execute action
                res = self.hands.execute(action, value if value else None)
                action_result += f" ({res})"
                # Remove tag from spoken reply (optional, but cleaner)
                if value:
                    reply = reply.replace(f"[ACTION: {action}: {value}]", "")
                else:
                    reply = reply.replace(f"[ACTION: {action}]", "")

        except Exception as e:
            print(f"[Brain Error] {e}", file=sys.stderr)
            reply = f"Brain freeze! {str(e)}"

        # Assign a conservative confidence value. If we had any image input, bump confidence slightly.
        confidence = 0.5
        if images_to_process:
            confidence = 0.65
        return {
            "response": reply.strip() + action_result,
            "mode": mode,
            "temporal_context": temporal_context,
            "confidence": confidence
        }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("text", help="User input text")
    parser.add_argument("--image", help="Path to webcam image file", default=None)
    parser.add_argument("--screen", help="Path to screen capture file", default=None)
    parser.add_argument("--user", help="User name", default="Jain")
    args = parser.parse_args()
    
    brain = FridayBrain(user_name=args.user)
    response = brain.think(args.text, image_path=args.image, screen_path=args.screen)
    # Only print final JSON to stdout; debugging and logs should go to stderr.
    print(json.dumps(response))
