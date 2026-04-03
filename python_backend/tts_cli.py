import argparse
import sys
import os
from core.tts import synthesize

def main():
    parser = argparse.ArgumentParser(description="Kokoro TTS CLI")
    parser.add_argument("--text-file", required=True, help="Path to text file containing text to synthesize")
    parser.add_argument("--output", required=True, help="Path to output audio file (WAV)")
    parser.add_argument("--voice", default="am_adam", help="Voice ID")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed")
    parser.add_argument("--lang", default="en-us", help="Language code")
    parser.add_argument("--emotion", default="[NEUTRAL]", help="Emotion tag")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.text_file):
        print(f"Error: Text file not found: {args.text_file}", file=sys.stderr)
        sys.exit(1)
        
    try:
        with open(args.text_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
            
        if not text:
            print("Error: Text file is empty", file=sys.stderr)
            sys.exit(1)
            
        # Synthesize
        audio_bytes = synthesize(text, emotion=args.emotion, voice=args.voice, lang=args.lang)
        
        # Write to output
        with open(args.output, 'wb') as f:
            f.write(audio_bytes)
            
        print(f"Successfully generated audio at {args.output}")
        
    except Exception as e:
        print(f"Error during synthesis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
