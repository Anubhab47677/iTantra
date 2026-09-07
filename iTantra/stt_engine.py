"""
Module 1: Speech-to-Text (STT) Engine for iTantra
Powered by faster-whisper with Automatic Language Detection focused on English, Hindi, and Odia.
"""
import os
import wave
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import config

# Map ISO language codes to Human Readable Names
SUPPORTED_LANGUAGES = {
    "en": "English 🇬🇧",
    "hi": "Hindi (हिंदी) 🇮🇳",
    "or": "Odia (ଓଡ଼ିଆ) 🇮🇳"
}

class STTEngine:
    def __init__(self, model_size=config.WHISPER_MODEL_SIZE, device=config.DEVICE, compute_type=config.COMPUTE_TYPE):
        print(f"⚙️ Initializing STT Engine (Whisper '{model_size}' - {compute_type} on {device})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def record_mic(self, duration_sec=4, samplerate=config.SAMPLE_RATE):
        """Record audio directly from microphone."""
        print(f"🎤 Recording voice input for {duration_sec} seconds...")
        audio_data = sd.rec(int(duration_sec * samplerate), samplerate=samplerate, channels=config.CHANNELS, dtype='float32')
        sd.wait()
        return audio_data.flatten()

    def save_wav(self, audio_array, filepath=os.path.join(config.TEMP_AUDIO_DIR, "recorded_input.wav"), samplerate=config.SAMPLE_RATE):
        """Save numpy audio array to a standard 16-bit PCM WAV file."""
        audio_int16 = (audio_array * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(config.CHANNELS)
            wf.setsampwidth(config.AUDIO_FORMAT_BITS // 8)
            wf.setframerate(samplerate)
            wf.writeframes(audio_int16.tobytes())
        return filepath

    def transcribe_file(self, audio_filepath):
        """Transcribe audio file with Automatic Language Detection (English, Hindi, Odia)."""
        # Automatic language detection by Whisper
        segments, info = self.model.transcribe(audio_filepath)
        text_result = "".join([segment.text for segment in segments]).strip()
        
        detected_code = info.language
        lang_name = SUPPORTED_LANGUAGES.get(detected_code, f"{detected_code.upper()} (Detected)")
        
        return {
            "text": text_result,
            "language": detected_code,
            "language_name": lang_name,
            "language_probability": round(info.language_probability, 4),
            "duration": round(info.duration, 2)
        }

    def process_mic_input(self, duration_sec=4):
        """Record from mic -> Save -> Auto Detect Language & Transcribe."""
        audio = self.record_mic(duration_sec=duration_sec)
        wav_path = self.save_wav(audio)
        result = self.transcribe_file(wav_path)
        result["raw_audio_bytes"] = len(audio.tobytes()) * 2
        return result, wav_path

if __name__ == "__main__":
    stt = STTEngine()
    print("STT Engine initialized with English, Hindi, and Odia support!")
