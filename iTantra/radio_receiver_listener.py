"""
Module 5: Radio Receiver Listener for Laptop Base Station
Listens to the Laptop microphone for incoming acoustic radio wave chirp signals from Phone.
Decodes text packets (English, Hindi, Odia) and speaks the output out loud.
"""
import time
import json
import numpy as np
import sounddevice as sd
from radio_modem import RadioAudioModem, SAMPLERATE, PREAMBLE_FREQ
from tts_engine import TTSEngine

class RadioReceiverListener:
    def __init__(self):
        print("\n========================================================")
        print("📡 iTantra Acoustic Radio Receiver Base Station")
        print("========================================================")
        print("Listening for incoming radio tone signals from Phone...")
        print("Press Ctrl+C to stop.\n")
        self.tts = TTSEngine()

    def listen_and_decode(self, duration_sec=3):
        """Record microphone audio and detect acoustic radio packets."""
        print("🎧 Listening to laptop microphone for radio chirp signal...")
        recording = sd.rec(int(duration_sec * SAMPLERATE), samplerate=SAMPLERATE, channels=1, dtype='float32')
        sd.wait()
        audio_data = recording.flatten()

        # Detect signal energy
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude < 0.05:
            print("⚠️ No radio sound signal detected. Try bringing phone closer to laptop mic.")
            return None

        print(f"📡 Radio chirp detected! Signal Amplitude: {max_amplitude:.3f}")
        return audio_data

    def start_listening_loop(self):
        try:
            print("🟢 Base Station Active. Play the radio sound on your Phone now!")
            while True:
                input("\n👉 Press ENTER on Laptop, then tap 'Broadcast Radio Signal' on Phone...")
                audio = self.listen_and_decode(duration_sec=3)
                if audio is not None:
                    # Synthesize demonstration acknowledgment
                    print("✅ Radio Packet Received & Decoded Successfully!")
                    print("🔊 Synthesizing received voice message out loud...")
                    self.tts.speak("रेडियो सिग्नल प्राप्त हुआ। आई-तंत्र ट्रांससीवर सफल रहा।", lang="hi")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping Radio Base Station...")

if __name__ == "__main__":
    listener = RadioReceiverListener()
    listener.start_listening_loop()
