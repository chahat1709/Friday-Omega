import os
import io
import numpy as np

# Safe imports — prevent crash if dependencies are missing
try:
    import soundfile as sf
    _HAS_SOUNDFILE = True
except ImportError:
    sf = None
    _HAS_SOUNDFILE = False

try:
    from kokoro_onnx import Kokoro
    _HAS_KOKORO = True
except ImportError:
    Kokoro = None
    _HAS_KOKORO = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

class TTSEngine:
    def __init__(self):
        self.kokoro = None
        self.pyttsx3_engine = None
        
        # Try Kokoro first
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_path = os.path.join(base_path, "models", "kokoro-v0_19.onnx")
        voices_path = os.path.join(base_path, "models", "voices.json")
        
        if _HAS_KOKORO and os.path.exists(model_path) and os.path.exists(voices_path):
            try:
                self.kokoro = Kokoro(model_path, voices_path)
                print("[TTS] Kokoro ONNX loaded successfully.")
            except Exception as e:
                print(f"[TTS] Kokoro init failed (pickle/version issue): {e}. Using fallback.")
        
        # Fallback to pyttsx3
        if not self.kokoro and PYTTSX3_AVAILABLE:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                # Set properties for faster response
                self.pyttsx3_engine.setProperty('rate', 180)  # Speed
                self.pyttsx3_engine.setProperty('volume', 0.9)
            except Exception as e:
                print(f"pyttsx3 TTS Init Error: {e}")

    def synthesize(self, text: str, emotion: str = "[NEUTRAL]", voice: str = "am_adam", lang: str = "en-us") -> bytes:
        # Prefer Kokoro for quality
        if self.kokoro:
            return self._synthesize_kokoro(text, emotion, voice, lang)
        elif self.pyttsx3_engine:
            return self._synthesize_pyttsx3(text, lang)
        else:
            return b""

    def _synthesize_pyttsx3(self, text: str, lang: str) -> bytes:
        # Set voice based on lang
        voices = self.pyttsx3_engine.getProperty('voices')
        if lang.startswith('en'):
            # Use English voice
            for v in voices:
                if 'english' in v.name.lower() or 'zira' in v.name.lower() or 'david' in v.name.lower():
                    self.pyttsx3_engine.setProperty('voice', v.id)
                    break
        elif lang == 'hi':
            # Try Hindi voice if available
            for v in voices:
                if 'hindi' in v.name.lower() or 'indian' in v.name.lower():
                    self.pyttsx3_engine.setProperty('voice', v.id)
                    break
        # Add more lang support as needed
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        self.pyttsx3_engine.save_to_file(text, temp_path)
        self.pyttsx3_engine.runAndWait()
        
        # Read the file
        with open(temp_path, 'rb') as f:
            data = f.read()
        
        # Cleanup
        os.unlink(temp_path)
        return data

    def _synthesize_kokoro(self, text: str, emotion: str, voice: str, lang: str) -> bytes:
        # Map emotion to speed/voice traits if possible
        # Kokoro doesn't support direct emotion tags yet, but we can tweak speed
        speed = 1.0
        if emotion == "[EXCITED]": speed = 1.1
        elif emotion == "[SAD]": speed = 0.9
        elif emotion == "[SKEPTICAL]": speed = 0.95
        
        # Generate
        samples, sample_rate = self.kokoro.create(
            text, 
            voice=voice, 
            speed=speed, 
            lang=lang
        )

        # Convert to WAV bytes
        byte_io = io.BytesIO()
        sf.write(byte_io, samples, sample_rate, format='WAV')
        byte_io.seek(0)
        return byte_io.getvalue()

# Global instance
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine

def synthesize(text: str, emotion: str = "[NEUTRAL]", voice: str = "am_adam", lang: str = "en-us") -> bytes:
    """
    Public API to synthesize text.
    """
    engine = get_engine()
    return engine.synthesize(text, emotion, voice, lang)
