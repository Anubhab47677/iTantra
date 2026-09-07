import os
import sys
import jiwer
from faster_whisper import WhisperModel

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_SIZE = "small"

def load_model():
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

def transcribe_text(model, audio_path, language=None):
    segments, info = model.transcribe(audio_path, beam_size=5, language=language)
    return "".join(seg.text for seg in segments).strip(), info.language

def benchmark(model, audio_path, reference_text, language=None):
    hypothesis, detected_lang = transcribe_text(model, audio_path, language)

    wer = jiwer.wer(reference_text, hypothesis)
    cer = jiwer.cer(reference_text, hypothesis)

    print(f"Detected language : {detected_lang}")
    print(f"Reference         : {reference_text}")
    print(f"Hypothesis        : {hypothesis}")
    print(f"WER               : {wer:.2%}")
    print(f"CER               : {cer:.2%}")
    return {"language": detected_lang, "reference": reference_text,
            "hypothesis": hypothesis, "wer": wer, "cer": cer}

if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_clip.wav"
    audio_path = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "datasets", filename))

    print("Enter the REFERENCE text (exactly what you said in the recording):")
    reference = input("> ")

    model = load_model()
    benchmark(model, audio_path, reference)