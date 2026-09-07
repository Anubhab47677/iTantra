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
  { code: "mix", bcp47: "en-IN", name: "Code-Mixed (Auto)", native: "Multilingual (मिश्रित / মিশ্র / கலப்பு)" },
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

/** Detects mixed Unicode scripts (Latin, Devanagari, Bengali, Tamil) in a single sentence */
export function detectScriptMixing(text: string): { isMixed: boolean; primaryBCP47: string } {
  const hasLatin = /[a-zA-Z]/.test(text);
  const hasDevanagari = /[\u0900-\u097F]/.test(text);
  const hasBengali = /[\u0980-\u09FF]/.test(text);
  const hasTamil = /[\u0B80-\u0BFF]/.test(text);

  const activeScriptsCount = [hasLatin, hasDevanagari, hasBengali, hasTamil].filter(Boolean).length;
  const isMixed = activeScriptsCount > 1;

  // Determine optimal base BCP47 voice for code-mixed speech
  let primaryBCP47 = "en-IN";
  if (hasBengali && !hasLatin && !hasDevanagari) primaryBCP47 = "bn-IN";
  else if (hasTamil && !hasLatin && !hasDevanagari) primaryBCP47 = "ta-IN";
  else if (hasDevanagari && !hasLatin) primaryBCP47 = "hi-IN";
  else if (isMixed) primaryBCP47 = "en-IN"; // en-IN and hi-IN handle Hinglish/Benglish/Tanglish code-mixing naturally

  return { isMixed, primaryBCP47 };
}

/** Analyzes speech text to detect emergency urgency level across ALL languages simultaneously */
export function detectUrgency(text: string, isAlert: boolean): number {
  if (isAlert) return 2;
  const lower = text.toLowerCase();
  const urgentKeywords = [
    // English
    "help", "danger", "emergency", "sos", "alert", "mayday", "urgent", "flood", "fire", "evacuate", "rescue",
    // Hindi
    "आपातकालीन", "बचाव", "खतरा", "मदद", "सहायता", "बाढ़", "आग",
    // Bengali
    "জরুরি", "সাহায্য", "বিপদ", "বন্যা", "আগুন", "উদ্ধার",
    // Tamil
    "அவசரம்", "உதவி", "ஆபத்து", "வெள்ளம்", "தீ"
  ];
  const hasKeyword = urgentKeywords.some((kw) => lower.includes(kw));
  const hasExclamation = text.includes("!");
  if (hasKeyword || hasExclamation) return 1;
  return 0;
}

/** Plays a tactical 2-tone radio emergency alert sound using Web Audio API */
function playTacticalAlertChime() {
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
  rec.continuous = false; // PTT single-phrase Walkie-Talkie mode
  rec.interimResults = true;
  return rec;
}

// Pre-warm browser voices on page load
if (typeof window !== "undefined" && "speechSynthesis" in window) {
  try {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  } catch (e) {}
}

export function speak(rawText: string, bcp47: string, alert: boolean, urgencyLevel?: number) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  
  // Clean text: strip any leading ASCII headers
  const text = rawText
    .replace(/^\[.*?\]\s*/g, "")
    .replace(/^[A-Z0-9_\-\s\(\)]+:\s*/gi, "")
    .trim();

  if (!text) return;

  // Unmute / resume speech synthesis if paused by browser autoplay policy
  try {
    if (window.speechSynthesis.paused || window.speechSynthesis.pending) {
      window.speechSynthesis.resume();
    }
  } catch (e) {}

  const urgency = urgencyLevel ?? detectUrgency(text, alert);

  // Play emergency alert chime if message is urgent
  if (urgency > 0) {
    playTacticalAlertChime();
  }

  // Analyze script mixing
  const { isMixed, primaryBCP47 } = detectScriptMixing(text);
  const targetBCP47 = isMixed || bcp47 === "en-IN" ? primaryBCP47 : bcp47;

  const voices = window.speechSynthesis.getVoices();
  const langPrefix = (targetBCP47.split("-")[0] || "en").toLowerCase();

  // Find exact or language prefix or native name match
  let match = voices.find((v) => v.lang.replace("_", "-").toLowerCase() === targetBCP47.toLowerCase()) ||
              voices.find((v) => v.lang.toLowerCase().startsWith(langPrefix)) ||
              voices.find((v) => v.name.toLowerCase().includes(langPrefix) ||
                (langPrefix === "bn" && (v.name.toLowerCase().includes("bengali") || v.name.toLowerCase().includes("bangla"))) ||
                (langPrefix === "ta" && v.name.toLowerCase().includes("tamil"))
              );

  // Fallback for systems without native voice packs installed
  let resolvedLang = targetBCP47;
  if (!match && (langPrefix === "bn" || langPrefix === "ta")) {
    const fallbackVoice = voices.find((v) => v.lang.toLowerCase().startsWith("hi")) ||
                          voices.find((v) => v.lang.toLowerCase().startsWith("en")) ||
                          voices[0];
    if (fallbackVoice) {
      match = fallbackVoice;
      resolvedLang = fallbackVoice.lang;
      console.warn(`[iTantra Voice] No native ${targetBCP47} voice installed on OS. Falling back to: ${fallbackVoice.name} (${fallbackVoice.lang})`);
    }
  }

  const u = new SpeechSynthesisUtterance(text);
  u.lang = match ? match.lang : resolvedLang;
  if (match) {
    u.voice = match;
  }
  u.volume = 1.0;

  // Optimal cadence & pitch tuning for high voice clarity
  if (urgency >= 2) {
    u.rate = 1.25;  // Fast, clear urgent tempo
    u.pitch = 1.30;
  } else if (urgency === 1) {
    u.rate = 1.10;
    u.pitch = 1.15;
  } else {
    // Slightly relaxed 0.95 rate for Bengali/Tamil/Code-Mixed clarity
    u.rate = (langPrefix === "bn" || langPrefix === "ta" || isMixed) ? 0.95 : 1.0;
    u.pitch = 1.0;
  }

  // Error recovery handler
  u.onerror = (evt) => {
    console.error(`[iTantra Voice] Speech synthesis error for ${targetBCP47}:`, evt);
    if (match && resolvedLang !== "en-IN") {
      console.log(`[iTantra Voice] Retrying speech with fallback en-IN voice`);
      const fallbackU = new SpeechSynthesisUtterance(text);
      fallbackU.lang = "en-IN";
      fallbackU.rate = 0.95;
      fallbackU.volume = 1.0;
      window.speechSynthesis.speak(fallbackU);
    }
  };

  if (urgency > 0 || alert) {
    window.speechSynthesis.cancel();
  }
  
  console.log(`[iTantra Voice] Speaking text (${targetBCP47}, voice=${match ? match.name : "default"}, mixed=${isMixed}, urgency=${urgency}): "${text}"`);
  window.speechSynthesis.speak(u);
}
