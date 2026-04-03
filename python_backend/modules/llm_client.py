"""LLM client abstraction (stub).
This module centralizes model loading and inference. For now it's a thin wrapper
that will call into existing core.llm.LLMEngine when available.
"""
import os
try:
    from core.llm import LLMEngine
except Exception:
    LLMEngine = None


class LLMClient:
    def __init__(self):
        # Resolve model path from env or common locations
        model_path = os.environ.get("LLM_MODEL_PATH")
        if not model_path:
            # Project-root relative candidate (python_backend/models/...)
            base = os.path.dirname(os.path.dirname(__file__))
            candidates = [
                os.path.join(base, "models", "qwen2.5-coder-7b-instruct-q4_k_m.gguf"),
                os.path.join(base, "..", "models", "qwen2.5-coder-7b-instruct-q4_k_m.gguf"),
            ]
            for c in candidates:
                if os.path.exists(c):
                    model_path = c
                    break

        if LLMEngine and model_path:
            try:
                self.engine = LLMEngine(model_path)
            except Exception as e:
                print(f"LLMEngine init failed: {e}")
                self.engine = None
        else:
            self.engine = None

    def generate(self, prompt: str, **kwargs) -> str:
        if not self.engine:
            return "[LLM not available]"
        return self.engine.generate(prompt)

    def generate_with_image(self, system_prompt: str, user_prompt: str, image_base64: str) -> str:
        if not self.engine:
            return "[Vision LLM not available]"
        # Leverage LLMEngine's multimodal method if available
        try:
            return self.engine.generate_with_image(system_prompt, user_prompt, image_base64)
        except Exception:
            return "[generate_with_image not supported by underlying LLM]"
