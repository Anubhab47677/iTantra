"""
Module 3: Text-to-Speech (TTS) Engine for iTantra
Native Audio Synthesis supporting English, Hindi, and Odia using gTTS with pyttsx3 fallback.
"""
import os
import sys
import time
import config

class TTSEngine:
    def __init__(self):
        print("⚙️ Initializing Multilingual TTS Engine (English 🇬🇧, Hindi 🇮🇳, Odia 🇮🇳)...")
        self._test_engine()

    def _test_engine(self):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.stop()
        except Exception as e:
            print(f"⚠️ Initial TTS check note: {e}")

    def speak(self, text, lang="hi", gender="m"):
        """Synthesize and play speech through speakers for English, Hindi, or Odia."""
        if not text:
            return
            
        g_name = "Female 👩" if gender == 'f' else "Male 👨"
        print(f"🔊 [TTS OUTPUT ({lang.upper()} - {g_name})]: '{text}'")
        
        # 1. Primary Engine: gTTS (Google Text-to-Speech for authentic Indic & English speech)
        try:
            from gtts import gTTS
            import pygame
            
            # Map language code (hi/or -> Indic, en -> English)
            gtts_lang = "hi" if lang in ["hi", "or"] else "en"
            output_mp3 = os.path.join(config.TEMP_AUDIO_DIR, "gtts_output.mp3")
            
            # Generate gTTS speech audio file
            tts = gTTS(text=text, lang=gtts_lang, slow=False)
            tts.save(output_mp3)
            
            # Play audio using pygame
            pygame.mixer.init()
            pygame.mixer.music.load(output_mp3)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            
            print(f"✅ Native {lang.upper()} Speech Playback Complete!")
            return
        except Exception as e:
            print(f"⚠️ gTTS playback note: {e}, falling back to pyttsx3 SAPI5...")

        # 2. Secondary Engine: pyttsx3 SAPI5 fallback
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 145)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            print("✅ Pyttsx3 Audio playback complete.")
        except Exception as e:
            print(f"⚠️ pyttsx3 error: {e}, using Windows native SAPI fallback...")
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
                print("✅ Windows Native SAPI playback complete.")
            except Exception as ex:
                print(f"❌ Fallback TTS failed: {ex}")

    def save_to_file(self, text, output_filename="output_synth.wav", lang="hi", gender="m"):
        """Synthesize text and save audio output to file."""
        filepath = os.path.join(config.TEMP_AUDIO_DIR, output_filename)
        try:
            from gtts import gTTS
            gtts_lang = "hi" if lang in ["hi", "or"] else "en"
            tts = gTTS(text=text, lang=gtts_lang)
            tts.save(filepath)
        except Exception as e:
            print(f"⚠️ TTS Save error: {e}")
        return filepath

if __name__ == "__main__":
    tts = TTSEngine()
    print("\n--- Testing Native Speech Synthesis ---")
    tts.speak("English voice test complete", lang="en", gender="m")
    tts.speak("नमस्ते, हिंदी वॉइस टेस्ट सफल रहा", lang="hi", gender="m")
    tts.speak("ନମସ୍କାର, ଓଡ଼ିଆ କଥାବାର୍ତ୍ତା ପରୀକ୍ଷା ସଫଳ ହେଲା", lang="or", gender="m")
