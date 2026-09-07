export type Lang = {
  code: string;
  bcp47: string;
  name: string;
  native: string;
};

export const LANGUAGES: Lang[] = [
  { code: "en", bcp47: "en-IN", name: "English", native: "English" },
  { code: "hi", bcp47: "hi-IN", name: "Hindi", native: "हिन्दी" },
  { code: "bn", bcp47: "bn-IN", name: "Bengali", native: "বাংলা" },
  { code: "ta", bcp47: "ta-IN", name: "Tamil", native: "தமிழ்" },
  { code: "mix", bcp47: "hi-IN", name: "Code-Mixed (Auto)", native: "Multilingual (मिश्रित / মিশ্র / கலப்பு)" },
];

/** Simplex VHF-style channel plan used by the radio set. */
export const CHANNELS = [
  { id: 1, mhz: 145.875, tag: "CH 1 · LINK" },
  { id: 2, mhz: 146.125, tag: "CH 2 · FIELD" },
  { id: 3, mhz: 146.375, tag: "CH 3 · EMERGENCY" },
];

export type Packet = {
  id: string;
  text: string;
  lang: string;
  mhz: number;
  priority: "routine" | "alert";
  urgency?: number; // 0 = normal, 1 = urgent, 2 = critical sos
  sentAt: number;
  bytes: number;
  station: string;
};

export const CHANNEL_NAME = "itantra-link";

export function encodedBytes(text: string) {
  return new TextEncoder().encode(text).length;
}

/** Converts Devanagari/Indic transliterated English words back to English script (Latin) while leaving native Indic words untouched */
export function normalizeCodeMixedText(rawText: string): string {
  if (!rawText) return "";
  let text = rawText;

  // Complete Hinglish/Indic Devanagari-to-English Script Mapping Table
  const transliterationMap: [RegExp, string][] = [
    // Multi-word Phrases
    [/\bआई नीड हेल्प\b/gi, "I need Help"],
    [/\bहेल्प आई नीड हेल्प\b/gi, "Help I need Help"],
    [/\bआई नीड\b/gi, "I need"],
    [/\bयू नीड\b/gi, "You need"],
    [/\bवी नीड\b/gi, "We need"],
    [/\bतेरे इस ए\b/gi, "There is a"],
    [/\bदेअर इज ए\b/gi, "There is a"],
    [/\bदेयर इज ए\b/gi, "There is a"],
    [/\bवाटर लेवल\b/gi, "Water Level"],
    [/\bवॉटर लेवल\b/gi, "Water Level"],
    [/\bथैंक यू\b/gi, "Thank you"],
    [/\bथैंक्स\b/gi, "Thanks"],

    // Core English Words in Devanagari
    [/\bआई\b/gi, "I"],
    [/\bनीड\b/gi, "need"],
    [/\bहेल्प\b/gi, "Help"],
    [/\bअर्जेंट\b/gi, "Urgent"],
    [/\bअर्जेन्ट\b/gi, "Urgent"],
    [/\bइमरजेंसी\b/gi, "Emergency"],
    [/\bइमरजेन्सी\b/gi, "Emergency"],
    [/\bएसओएस\b/gi, "SOS"],
    [/\bअलर्ट\b/gi, "Alert"],
    [/\bडेंजर\b/gi, "Danger"],
    [/\bडेन्जर\b/gi, "Danger"],
    [/\bफ्लड\b/gi, "Flood"],
    [/\bरेस्क्यू\b/gi, "Rescue"],
    [/\bवाटर\b/gi, "Water"],
    [/\bवॉटर\b/gi, "Water"],
    [/\bलेवल\b/gi, "Level"],
    [/\bसेक्टर\b/gi, "Sector"],
    [/\bहेल्पलाइन\b/gi, "Helpline"],
    [/\bलोकेशन\b/gi, "Location"],
    [/\bसिचुएशन\b/gi, "Situation"],
    [/\bटीम\b/gi, "Team"],
    [/\bकॉल\b/gi, "Call"],
    [/\bमैसेज\b/gi, "Message"],
    [/\bसिग्नल\b/gi, "Signal"],
    [/\bरेडियो\b/gi, "Radio"],
    [/\bक्लियर\b/gi, "Clear"],
    [/\bओके\b/gi, "OK"],
    [/\bहेलो\b/gi, "Hello"],
    [/\bहॅलो\b/gi, "Hello"],
    [/\bप्लीज\b/gi, "Please"],
    [/\bफास्ट\b/gi, "Fast"],
    [/\bक्विक\b/gi, "Quick"],
    [/\bनाउ\b/gi, "Now"],
    [/\bइज\b/gi, "is"],
    [/\bइन\b/gi, "in"],
    [/\bऑन\b/gi, "on"],
    [/\bएट\b/gi, "at"],
    [/\bफॉर\b/gi, "for"],
    [/\bविद\b/gi, "with"],
    [/\bफ्रॉम\b/gi, "from"],
    [/\bटू\b/gi, "to"],
    [/\bएंड\b/gi, "and"],
    [/\bऑर\b/gi, "or"],
    [/\bबट\b/gi, "but"],
    [/\bसो\b/gi, "so"],
    [/\bयस\b/gi, "yes"],
    [/\bनो\b/gi, "no"],

    // Bengali transliterations
    [/\bহেল্প\b/gi, "Help"],
    [/\bইমারজেন্সি\b/gi, "Emergency"],
    [/\bএসওএস\b/gi, "SOS"],
    [/\bঅ্যালার্ট\b/gi, "Alert"],
    [/\bরেস্কিউ\b/gi, "Rescue"],

    // Tamil transliterations
    [/\bஹெல்ப்\b/gi, "Help"],
    [/\bஎமர்ஜென்சி\b/gi, "Emergency"]
  ];

  for (const [regex, replacement] of transliterationMap) {
    text = text.replace(regex, replacement);
  }

  return text;
}

/** Detects mixed Unicode scripts and selects the native voice while preserving 100% of original text script */
export function detectScriptMixing(text: string): { isMixed: boolean; primaryBCP47: string } {
  const hasLatin = /[a-zA-Z]/.test(text);
  const hasDevanagari = /[\u0900-\u097F]/.test(text);
  const hasBengali = /[\u0980-\u09FF]/.test(text);
  const hasTamil = /[\u0B80-\u0BFF]/.test(text);

  const activeScriptsCount = [hasLatin, hasDevanagari, hasBengali, hasTamil].filter(Boolean).length;
  const isMixed = activeScriptsCount > 1;

  // Select voice target based on dominant native script in the mixed sentence
  let primaryBCP47 = "hi-IN";
  if (hasBengali) primaryBCP47 = "bn-IN";
  else if (hasTamil) primaryBCP47 = "ta-IN";
  else if (hasDevanagari) primaryBCP47 = "hi-IN";
  else if (hasLatin) primaryBCP47 = "en-IN";

  return { isMixed, primaryBCP47 };
}

/** Analyzes speech text to detect emergency urgency level across ALL 4 languages & transliterated Indic scripts */
export function detectUrgency(text: string, isAlert: boolean): number {
  if (isAlert) return 2;
  const lower = text.toLowerCase();
  const urgentKeywords = [
    // English
    "help", "danger", "emergency", "sos", "alert", "mayday", "urgent", "flood", "fire", "evacuate", "rescue", "need",
    // Hindi Native
    "आपातकालीन", "बचाव", "खतरा", "मदद", "सहायता", "बाढ़", "आग",
    // Devanagari Transliterated
    "हेल्प", "अर्जेंट", "अर्जेन्ट", "इमरजेंसी", "एसओएस", "अलर्ट", "डेंजर", "डेन्जर", "फ्लड", "रेस्क्यू", "नीड", "हेल्पलाइन",
    // Bengali Native & Transliterated
    "জরুরি", "সাহায্য", "বিপদ", "বন্যা", "আগুন", "উদ্ধার", "হেল্প", "ইমারজেন্সি", "এসওএস", "অ্যালার্ট", "রেস্কিউ",
    // Tamil Native & Transliterated
    "அவசரம்", "உதவி", "ஆபத்து", "வெள்ளம்", "தீ", "ஹெல்ப்", "எமர்ஜென்சி"
  ];
  const hasKeyword = urgentKeywords.some((kw) => lower.includes(kw.toLowerCase()));
  const hasExclamation = text.includes("!");
  if (hasKeyword || hasExclamation) return 1;
  return 0;
}

/** Plays a tactical 2-tone radio emergency alert sound using Web Audio API */
export function playTacticalAlertChime() {
  if (typeof window === "undefined") return;
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = "sawtooth";
    osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 tone
    osc.frequency.setValueAtTime(1200, ctx.currentTime + 0.12); // High urgent tone

    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + 0.3);
  } catch (e) {
    // Web audio fallback
  }
}

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives?: number;
  start: () => void;
  stop: () => void;
  onresult: ((e: any) => void) | null;
  onerror: ((e: any) => void) | null;
  onend: (() => void) | null;
};

export function createRecognizer(lang: string): SpeechRecognitionLike | null {
  if (typeof window === "undefined") return null;
  const Ctor =
    (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (!Ctor) return null;
  const rec: SpeechRecognitionLike = new Ctor();
  rec.lang = lang;
  rec.continuous = true; // Continuous listening so speech pauses do not truncate sentences
  rec.interimResults = true;
  rec.maxAlternatives = 3;
  return rec;
}

// Pre-warm browser voices & register mobile autoplay unlock listener
let cachedVoices: SpeechSynthesisVoice[] = [];

if (typeof window !== "undefined" && "speechSynthesis" in window) {
  try {
    const loadVoices = () => {
      cachedVoices = window.speechSynthesis.getVoices();
    };
    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;

    // Mobile/Browser Autoplay unlock listener on any user interaction
    const unlockAudio = () => {
      try {
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
        }
      } catch (e) {}
    };
    window.addEventListener("touchstart", unlockAudio);
    window.addEventListener("click", unlockAudio);
    window.addEventListener("keydown", unlockAudio);
  } catch (e) {}
}

export function speak(rawText: string, bcp47: string, alert: boolean, urgencyLevel?: number) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  
  // Clean text and normalize transliterated English words into English script
  const text = normalizeCodeMixedText(
    rawText.replace(/^\[.*?\]\s*/g, "").replace(/^[A-Z0-9_\-\s\(\)]+:\s*/gi, "").trim()
  );

  if (!text) return;

  const urgency = urgencyLevel ?? detectUrgency(text, alert);

  // Play audio alert chime ONLY for urgent messages to prevent sound card driver glitching
  if (urgency > 0) {
    playTacticalAlertChime();
  }

  // Clear previous speech only if currently speaking
  try {
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
  } catch (e) {}

  // Analyze script mixing and pick native voice engine while keeping original script
  const { isMixed, primaryBCP47 } = detectScriptMixing(text);
  const targetBCP47 = isMixed ? primaryBCP47 : (bcp47 || "hi-IN");

  let voices = cachedVoices.length ? cachedVoices : window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) {
    voices = window.speechSynthesis.getVoices();
  }
  const langPrefix = (targetBCP47.split("-")[0] || "hi").toLowerCase();

  // Find exact or language prefix or native name match across installed voices
  let match = voices.find((v) => v.lang.replace("_", "-").toLowerCase() === targetBCP47.toLowerCase()) ||
              voices.find((v) => v.lang.toLowerCase().startsWith(langPrefix)) ||
              voices.find((v) => v.name.toLowerCase().includes(langPrefix) ||
                (langPrefix === "bn" && (v.name.toLowerCase().includes("bengali") || v.name.toLowerCase().includes("bangla"))) ||
                (langPrefix === "ta" && v.name.toLowerCase().includes("tamil"))
              );

  // Guaranteed audio playback fallback when device lacks native voice pack
  let selectedVoice = match;
  let selectedLang = match ? match.lang : "hi-IN";

  if (!match) {
    const fallbackVoice = voices.find((v) => v.lang.toLowerCase().startsWith("hi")) ||
                          voices.find((v) => v.lang.toLowerCase().startsWith("en")) ||
                          voices[0];
    if (fallbackVoice) {
      selectedVoice = fallbackVoice;
      selectedLang = fallbackVoice.lang;
    } else {
      selectedLang = "hi-IN";
    }
  }

  const u = new SpeechSynthesisUtterance(text);
  u.lang = selectedLang;
  if (selectedVoice) {
    u.voice = selectedVoice;
  }
  u.volume = 1.0;
  u.rate = 1.0;
  u.pitch = urgency >= 2 ? 1.10 : (urgency === 1 ? 1.05 : 1.0);

  u.onerror = (evt) => {
    console.error(`[iTantra Voice] Error:`, evt);
    try {
      const fallbackU = new SpeechSynthesisUtterance(text);
      fallbackU.lang = "hi-IN";
      window.speechSynthesis.speak(fallbackU);
    } catch (err) {}
  };

  console.log(`[iTantra Voice] Clean speech dispatch: "${text}" (${selectedLang})`);
  
  // Synchronous execution satisfying browser user gesture autoplay requirements
  try {
    window.speechSynthesis.speak(u);
  } catch (err) {
    console.error("[iTantra Voice] Synchronous speak error:", err);
  }
}
