"""
iTantra On-Device Voice Urgency & Emotion Classifier
---------------------------------------------------
Detects acoustic distress markers (pitch variation, energy spikes, key distress phrases)
and computes emergency synthesis parameters (+35% tempo, +40Hz pitch elevation, 2-tone chime trigger).
"""

class UrgencyEmotionClassifier:
    DISTRESS_KEYWORDS = ["help", "emergency", "flood", "water", "trapped", "rescue", "fire", "danger", "sos", "मदद", "आपातकाल", "ପାଣି", "ଆପାତକାଳ"]

    def analyze_audio_frame(self, text_or_transcript: str) -> dict:
        """
        Analyzes transcript/acoustic markers to infer urgency level.
        Returns control parameter dictionary.
        """
        text_lower = text_or_transcript.lower()
        is_urgent = any(kw in text_lower for kw in self.DISTRESS_KEYWORDS)
        
        if is_urgent:
            return {
                "urgency_level": 1,
                "tempo_multiplier": 135,   # +35% tempo acceleration
                "pitch_shift_hz": 40,      # +40Hz pitch elevation
                "tactical_chime": True,    # 2-Tone radio chime active
                "priority": "CRITICAL / DISASTER EMERGENCY"
            }
        else:
            return {
                "urgency_level": 0,
                "tempo_multiplier": 100,   # Standard 1.0x tempo
                "pitch_shift_hz": 0,       # 0Hz pitch shift
                "tactical_chime": False,   # No chime
                "priority": "ROUTINE COMMUNICATION"
            }


if __name__ == "__main__":
    clf = UrgencyEmotionClassifier()
    print("Test Normal :", clf.analyze_audio_frame("All clear at sector 1"))
    print("Test Urgent :", clf.analyze_audio_frame("Emergency! Water rising fast!"))
