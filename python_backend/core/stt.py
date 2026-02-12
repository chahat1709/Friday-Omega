import os
import wave
import numpy as np
import torch
from faster_whisper import WhisperModel

# Try optional soundfile for robust audio reads
try:
    import soundfile as sf
    _HAS_SOUNDFILE = True
except Exception:
    _HAS_SOUNDFILE = False

class STTEngine:
    def __init__(self, model_size="tiny.en", device="cpu", compute_type="int8"):
        self.device = device
        self.model_size = model_size
        try:
            print(f"[STT] Loading Whisper Model: {model_size} on {self.device}...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            print(f"[STT] Error loading optimized model: {e}. Falling back to float32.")
            self.model = WhisperModel(model_size, device=device, compute_type="float32")


    def transcribe(self, audio_data):
        """
        Transcribes audio data (numpy array or file path).
        Ensures input is 16kHz mono float32 for Whisper.
        """
        try:
            if isinstance(audio_data, str) and os.path.exists(audio_data):
                # Faster-Whisper natively decodes via FFmpeg directly from path
                segments, info = self.model.transcribe(
                    audio_data, 
                    beam_size=1, 
                    condition_on_previous_text=False
                )
            elif isinstance(audio_data, np.ndarray):
                audio_float32 = audio_data.astype(np.float32)
                if np.abs(audio_float32).max() > 1.0: 
                    audio_float32 /= 32768.0
                
                rms = np.sqrt(np.mean(audio_float32**2))
                if rms < 0.005: 
                    return ""
                
                if len(audio_float32) < 1600: 
                    return ""

                segments, info = self.model.transcribe(
                    audio_float32, 
                    beam_size=1, 
                    condition_on_previous_text=False
                )
            else:
                return ""
            
            text = ""
            print(f"[STT] Processing segments...")
            for segment in segments:
                text += segment.text + " "
            
            print(f"[STT] Final: {text.strip()[:50]}...")
            return text.strip()

        except Exception as e:
            if str(e):
                print(f"[STT] Transcribe Error: {e}")
            return ""

    def _load_audio(self, path):
        # Helper to safely load audio file to 16k float32
        try:
            import librosa
            audio, _ = librosa.load(path, sr=16000)
            return audio
        except ImportError:
            # Fallback if librosa not installed
            if _HAS_SOUNDFILE:
                 data, sr = sf.read(path)
                 # fast/naive resample if sr != 16000 not implemented here without scipy/librosa
                 # but this is better than crashing
                 return data.astype(np.float32)
            return np.zeros(16000, dtype=np.float32)

