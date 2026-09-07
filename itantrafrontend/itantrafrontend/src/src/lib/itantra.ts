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
];

/** Simplex VHF-style channel plan used by the radio set. */
export const CHANNELS = [{ id: 1, mhz: 145.875, tag: "CH 1 · LINK" },
  { id: 2, mhz: 146.125, tag: "CH 2 · FIELD" },
  { id: 3, mhz: 146.375, tag: "CH 3 · EMERGENCY" },
];

export type Packet = {
  id: string;
  text: string;
  lang: string;
  mhz: number;
  priority: "routine" | "alert";
  sentAt: number;
  bytes: number;
  station: string;
};

export const CHANNEL_NAME = "itantra-link";

export function encodedBytes(text: string) {
  return new TextEncoder().encode(text).length;
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
  rec.continuous = true;
  rec.interimResults = true;
  return rec;
}

export function speak(text: string, bcp47: string, alert: boolean) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
  const u = new SpeechSynthesisUtterance(text);
  u.lang = bcp47;
  u.volume = 1;
  u.rate = alert ? 0.95 : 1;
  u.pitch = alert ? 1.15 : 1;
  const match = window.speechSynthesis
    .getVoices()
    .find((v) => v.lang.replace("_", "-") === bcp47);
  if (match) u.voice = match;
  if (alert) window.speechSynthesis.cancel();
  window.speechSynthesis.speak(u);
}
