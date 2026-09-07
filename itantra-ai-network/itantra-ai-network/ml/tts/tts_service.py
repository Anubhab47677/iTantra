import torch
import soundfile as sf
from transformers import VitsModel, AutoTokenizer

LANGUAGE_MODELS = {
    "hi": "facebook/mms-tts-hin",
    "bn": "facebook/mms-tts-ben",
    "ta": "facebook/mms-tts-tam",
    "en": "facebook/mms-tts-eng",
}

class TTSService:
    """
    Loads TTS models on first use per language, then reuses them.
    Unlike STT/Codec, TTS needs one model PER language, so we load
    lazily (only when that language is actually requested) and cache.
    """
    def __init__(self):
        self._models = {}   # language_code -> (model, tokenizer)

    def _get_model(self, language_code):
        if language_code not in self._models:
            if language_code not in LANGUAGE_MODELS:
                raise ValueError(f"No TTS model mapped for language '{language_code}'")
            model_id = LANGUAGE_MODELS[language_code]
            print(f"[TTS] Loading model for '{language_code}' ({model_id})...")
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = VitsModel.from_pretrained(model_id)
            model.eval()
            self._models[language_code] = (model, tokenizer)
            print(f"[TTS] Model for '{language_code}' loaded and cached.")
        return self._models[language_code]

    def synthesize(self, text, language_code, output_path):
        model, tokenizer = self._get_model(language_code)
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            output = model(**inputs).waveform
        audio = output.squeeze().numpy()
        sf.write(output_path, audio, model.config.sampling_rate)
        return output_path


if __name__ == "__main__":
    service = TTSService()
    service.synthesize("नमस्कार मैं अनुभव हूँ", "hi", "../../datasets/tts_service_test.wav")
    print("Saved successfully.")