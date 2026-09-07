import os
import sys
import time
import torch
import soundfile as sf
from transformers import VitsModel, AutoTokenizer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "..", "datasets"))

# MMS-TTS ships one model per language - map your target languages to their checkpoint IDs
LANGUAGE_MODELS = {
    "hi": "facebook/mms-tts-hin",   # Hindi
    "bn": "facebook/mms-tts-ben",   # Bengali
    "ta": "facebook/mms-tts-tam",   # Tamil
    "en": "facebook/mms-tts-eng",   # English
}

def load_tts(language_code):
    if language_code not in LANGUAGE_MODELS:
        raise ValueError(f"No TTS model mapped for language '{language_code}'")
    model_id = LANGUAGE_MODELS[language_code]
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    model.eval()
    return model, tokenizer

def synthesize(model, tokenizer, text, output_path):
    inputs = tokenizer(text, return_tensors="pt")

    start = time.time()
    with torch.no_grad():
        output = model(**inputs).waveform
    latency = time.time() - start

    audio = output.squeeze().numpy()
    sf.write(output_path, audio, model.config.sampling_rate)

    duration_sec = len(audio) / model.config.sampling_rate
    print(f"Text                : {text}")
    print(f"Synthesis latency   : {latency*1000:.1f} ms")
    print(f"Output duration     : {duration_sec:.2f}s")
    print(f"Real-time factor    : {latency/duration_sec:.3f}  (lower is better; <1.0 = faster than real-time)")
    print(f"Saved to            : {output_path}")

if __name__ == "__main__":
    language = sys.argv[1] if len(sys.argv) > 1 else "hi"
    text = sys.argv[2] if len(sys.argv) > 2 else "नमस्कार मैं अनुभव हूँ"
    output_path = os.path.join(DATASETS_DIR, f"tts_output_{language}.wav")

    model, tokenizer = load_tts(language)
    synthesize(model, tokenizer, text, output_path)