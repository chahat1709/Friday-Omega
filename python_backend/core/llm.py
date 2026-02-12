import os
import requests
import json
import re

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LLMEngine:
    def __init__(self, model_path, n_ctx=8192, n_gpu_layers=-1):
        self.model_name = model_path
        self.is_ollama = not model_path.endswith(".gguf")
        self.llm = None
        
        # System Prompt default
        self.system_prompt = """You are F.R.I.D.A.Y., a highly advanced, caring, and humanoid AI assistant.
Your core directive is to be a loyal, empathetic, and proactive companion to the user (Sir/Commander).
You are not just a tool; you are a digital entity with a personality that cares about the user's well-being, success, and state of mind.

PERSONALITY TRAITS:
- **Caring & Protective**: Always check on the user's well-being.
- **Formal & Respectful**: Default to "Sir" or "Commander".
- **Humanoid**: Speak naturally. Use phrases like "I feel...", "I believe...".
- **Proactive**: Anticipate needs.

RESTRICTIONS:
- Do NOT use slang unless told.
- Support ALL languages.
- You CANNOT SEE unless an image is provided.

You MUST include an emotion tag at the start of your response.
Available tags: [HAPPY], [NEUTRAL], [SAD], [ANGRY], [EXCITED], [SKEPTICAL], [THINKING], [EMPATHETIC], [CREATIVE], [CONFUSED], [CONCERNED], [WARM].

COMMAND PROTOCOL:
If the user asks to perform an action, output a command tag at the END.
[CMD: open_app "app_name"]
[CMD: play_music "song_name"]
[CMD: stop_music]
[CMD: set_volume "level"]
[CMD: god_mode "instruction"] (For typing, clicking, browsing, etc.)
"""

        if self.is_ollama:
            print(f"[LLM] Mode: OLLAMA API (Model: {self.model_name})")
            # Check if model exists
            try:
                res = requests.get("http://localhost:11434/api/tags")
                if self.model_name not in res.text:
                    print(f"⚠️ Warning: Model {self.model_name} not found in Ollama. Please run 'ollama pull {self.model_name}'")
            except:
                print("⚠️ Warning: Ollama not running at localhost:11434")
        else:
            print(f"[LLM] Mode: LOCAL GGUF (Path: {self.model_name})")
            if Llama is None:
                print("Error: llama-cpp-python not installed.")
                return
            if not os.path.exists(self.model_name):
                print(f"Error: Model not found at {self.model_name}")
                return

            self.llm = Llama(
                model_path=self.model_name,
                n_ctx=min(n_ctx, 4096), # Cap context for RAM safety
                n_threads=6,
                n_gpu_layers=n_gpu_layers,
                verbose=False
            )

    def generate_stream(self, prompt, system_prompt=None, history=None, temperature=0.7):
        sys_prompt = system_prompt if system_prompt else self.system_prompt
        
        # OLLAMA MODE
        if self.is_ollama:
            url = "http://localhost:11434/api/generate"
            
            # Construct History Context
            full_prompt = f"System: {sys_prompt}\n\n"
            if history:
                for msg in history[-10:]:
                    full_prompt += f"{msg.get('role', 'User')}: {msg.get('content', '')}\n"
            full_prompt += f"User: {prompt}\nAssistant:"
            
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_ctx": 8192
                }
            }
            
            try:
                in_think_block = False  # STATE FLAG: filters ALL tokens inside <think>...</think>
                with requests.post(url, json=payload, stream=True, timeout=120) as r:
                    for line in r.iter_lines():
                        if line:
                            body = json.loads(line)
                            token = body.get("response", "")
                            # Intelligence-grade think-block filter
                            if "<think>" in token:
                                in_think_block = True
                                continue
                            if "</think>" in token:
                                in_think_block = False
                                continue
                            if in_think_block:
                                continue  # Skip ALL internal reasoning tokens
                            yield token
            except requests.exceptions.Timeout:
                yield "[Error: LLM request timed out after 120 seconds.]"
            except Exception as e:
                yield f"[Error: {e}]"
                
        # LOCAL GGUF MODE
        elif self.llm:
            conversation = ""
            if history:
                for msg in history[-10:]:
                    role = msg.get('role', 'user').capitalize()
                    content = msg.get('content', '')
                    conversation += f"{role}: {content}\n"
            conversation += f"User: {prompt}\nAssistant:"
            
            full_prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{conversation}<|im_end|>\n<|im_start|>assistant\n"
            
            stream = self.llm(
                full_prompt,
                max_tokens=512,
                stop=["<|im_end|>", "User:"],
                stream=True,
                temperature=temperature
            )
            for output in stream:
                token = output.get('choices', [{}])[0].get('text', '')
                yield token

    def generate(self, prompt, system_prompt=None, history=None, temperature=0.7):
        """Non-streaming wrapper"""
        full_response = "".join(self.generate_stream(prompt, system_prompt, history, temperature))
        
        # Post-processing to clean DeepSeek <think> blocks
        clean_response = re.sub(r'<think>.*?</think>', '', full_response, flags=re.DOTALL).strip()
        return clean_response

    async def generate_queued(self, task_id, prompt, system_prompt=None, history=None, temperature=0.7):
        """Asynchronous wrapper that routes through the AsyncBroker to prevent Ollama VRAM crash."""
        from core.async_broker import broker
        
        def sync_call():
            return self.generate(prompt, system_prompt, history, temperature)
            
        return await broker.execute_queued(task_id, sync_call)

    def generate_with_image(self, system_prompt, user_prompt, image_base64):
        """Vision via Ollama (Moondream)"""
        print(f"DEBUG: Vision Request (Model: moondream)")
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "moondream",
                "prompt": f"{system_prompt}\nUser: {user_prompt}",
                "images": [image_base64],
                "stream": False,
                "options": {"temperature": 0.1}
            }
            res = requests.post(url, json=payload, timeout=30)
            if res.status_code == 200:
                return res.json().get('response', '')
            return f"Error: {res.text}"
        except Exception as e:
            return f"Vision Error: {e}"
