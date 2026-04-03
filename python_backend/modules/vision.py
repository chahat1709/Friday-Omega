"""Vision utilities (stub).
This module will hold screenshotting, grid overlay, and helpers for LLaVA.
"""
from PIL import ImageGrab
import io, base64

class Vision:
    @staticmethod
    def capture_screen() -> bytes:
        img = ImageGrab.grab()
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    @staticmethod
    def image_to_base64(img_bytes: bytes) -> str:
        return base64.b64encode(img_bytes).decode('utf-8')

    @staticmethod
    def analyze_image(image_base64: str, prompt: str = "Describe this image in detail.") -> str:
        """
        Sends the image to the local Ollama LLaVA model for analysis.
        """
        import requests
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": "llava",
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json().get("response", "No response from vision model.")
            else:
                return f"Vision Error: Status {response.status_code} - {response.text}"
        except Exception as e:
            return f"Vision Service Unavailable: {e}"
