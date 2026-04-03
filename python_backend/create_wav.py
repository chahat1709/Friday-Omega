import wave, struct, math

# Generate a clearer test tone: 1s at 440Hz, amplitude 0.6
sr = 16000
duration = 1.0
freq = 440
amplitude = 0.6
n = int(sr * duration)
out_path = 'python_backend/test_tone.wav'

with wave.open(out_path, 'w') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    for i in range(n):
        val = int(32767 * amplitude * math.sin(2 * math.pi * freq * i / sr))
        wf.writeframes(struct.pack('<h', val))

print(f'WAV created: {out_path}')
