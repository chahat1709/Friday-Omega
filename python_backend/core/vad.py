import os
import numpy as np
import onnxruntime as ort

class VADEngine:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
        self.session = None
        self._init_model()
        
    def _init_model(self):
        # Download or load Silero VAD ONNX model
        # For this example, we assume the model is at python_backend/models/silero_vad.onnx
        # If not, one would typically download it.
        model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "silero_vad.onnx")
        
        if not os.path.exists(model_path):
            print(f"VAD Model not found at {model_path}. Please download silero_vad.onnx")
            return

        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        
        # Use CPU for low latency VAD
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'], sess_options=opts)
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self.sample_rate = 16000

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        if self.session is None:
            return False
            
        # Audio chunk should be 512, 1024, or 1536 samples for Silero
        # Assuming 16khz mono
        
        # Prepare inputs
        input_data = {
            'input': audio_chunk.reshape(1, -1).astype(np.float32),
            'sr': np.array([16000], dtype=np.int64),
            'h': self._h,
            'c': self._c
        }
        
        # Run inference
        try:
             out, self._h, self._c = self.session.run(None, input_data)
             return out[0][0] > self.threshold
        except Exception as e:
             # Fallback to energy VAD if model inference fails
             rms = np.sqrt(np.mean(audio_chunk**2))
             return rms > 0.008

    def reset(self):
        self._h = np.zeros((2, 1, 64), dtype=np.float32)
        self._c = np.zeros((2, 1, 64), dtype=np.float32)
