import os
import sys
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000
DURATION = 5

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "datasets")
OUTPUT_DIR = os.path.normpath(OUTPUT_DIR)

def record(filename="test_clip.wav"):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)
    print(f"Recording for {DURATION} seconds... speak now.")
    try:
        audio = sd.rec(
            int(DURATION * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32"
        )
        sd.wait()
    except Exception as e:
        print("Recording failed:", e)
        return
    sf.write(output_path, audio, SAMPLE_RATE)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    # Optional command-line argument: python record_audio.py hindi_clip.wav
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_clip.wav"
    record(filename)