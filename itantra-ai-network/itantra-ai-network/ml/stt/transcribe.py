import os
import sys
from faster_whisper import WhisperModel

MODEL_SIZE = "small"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_model():
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    return model

def transcribe(model, audio_path, forced_language=None):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    # language=None means auto-detect; pass e.g. "hi" to force a language
    segments, info = model.transcribe(audio_path, beam_size=5, language=forced_language)
    print(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
    print("Transcript:")
    full_text = ""
    for segment in segments:
        print(f"  [{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")
        full_text += segment.text
    return full_text.strip()

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_clip.wav"
    audio_path = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "datasets", filename))

    model = load_model()
    print("--- Auto-detect ---")
    text = transcribe(model, audio_path)
    print("\nFull transcript:", text)