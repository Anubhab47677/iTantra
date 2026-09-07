import { useCallback, useEffect, useRef, useState } from "react";
import { Mic } from "lucide-react";
import {
  CHANNELS,
  CHANNEL_NAME,
  LANGUAGES,
  createRecognizer,
  encodedBytes,
  speak,
  type Packet,
} from "@/lib/itantra";

const STATION = `STN-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;

export function LinkConsole() {
  const [channel, setChannel] = useState(CHANNELS[0]!);
  const [lang, setLang] = useState(LANGUAGES[0]!);
  const [alertMode, setAlertMode] = useState(false);
  const [ptt, setPtt] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [live, setLive] = useState(false);
  const [interim, setInterim] = useState("");
  const [traffic, setTraffic] = useState<{ p: Packet; dir: "TX" | "RX" }[]>([]);
  const [supported, setSupported] = useState(true);
  const [latency, setLatency] = useState<number | null>(null);

  const recRef = useRef<ReturnType<typeof createRecognizer>>(null);
  const chanRef = useRef<BroadcastChannel | null>(null);
  const speechStart = useRef(0);
  const langRef = useRef(lang);
  langRef.current = lang;
  const mhzRef = useRef(channel.mhz);
  mhzRef.current = channel.mhz;

  useEffect(() => {
    setSupported(
      !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition),
    );
    const chan = new BroadcastChannel(CHANNEL_NAME);
    chanRef.current = chan;
    chan.onmessage = (e) => {
      const p = e.data as Packet;
      if (p.station === STATION) return;
      if (p.mhz !== mhzRef.current) return; // off-frequency: not received
      setTraffic((prev) => [{ p, dir: "RX" as const }, ...prev].slice(0, 30));
      const voice = LANGUAGES.find((l) => l.code === p.lang) ?? LANGUAGES[0]!;
      speak(p.text, voice.bcp47, p.priority === "alert");
    };
    return () => chan.close();
  }, []);

  const transmit = useCallback(
    (text: string) => {
      const clean = text.trim();
      if (!clean) return;
      const packet: Packet = {
        id: crypto.randomUUID(),
        text: clean,
        lang: langRef.current.code,
        mhz: mhzRef.current,
        priority: alertMode ? "alert" : "routine",
        sentAt: Date.now(),
        bytes: encodedBytes(clean),
        station: STATION,
      };
      chanRef.current?.postMessage(packet);
      setTraffic((prev) => [{ p: packet, dir: "TX" as const }, ...prev].slice(0, 30));
      setLatency(Date.now() - speechStart.current);
    },
    [alertMode],
  );

  const startTx = useCallback(() => {
    if (live) return;
    const rec = createRecognizer(langRef.current.bcp47);
    if (!rec) {
      setSupported(false);
      return;
    }
    recRef.current = rec;
    speechStart.current = Date.now();
    setLive(true);
    setInterim("");
    rec.onresult = (e: any) => {
      let partial = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) transmit(res[0].transcript);
        else partial += res[0].transcript;
      }
      setInterim(partial);
    };
    rec.onerror = () => setLive(false);
    rec.onend = () => setLive(false);
    rec.start();
  }, [live, transmit]);

  const stopTx = useCallback(() => {
    recRef.current?.stop();
    recRef.current = null;
    setLive(false);
    setInterim("");
  }, []);

  // PTT off = open (phone-style) mic that stays keyed.
  useEffect(() => {
    if (!ptt && !live) startTx();
    if (ptt && live) stopTx();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ptt]);

  return (
    <div className="mx-auto w-full max-w-sm">
      <div className="panel-surface rounded-3xl p-4">
        {/* readout */}
        <div className="rounded-2xl border border-etch bg-background/70 p-4">
          <div className="flex items-center justify-between">
            <span className="label-etch">{STATION}</span>
            <span
              className={`font-mono text-[10px] uppercase tracking-widest ${live ? "text-signal" : "text-accent"}`}
            >
              {live ? "● CONNECTED" : "○ STANDBY"}
            </span>
          </div>
          <p className="mt-2 font-mono text-4xl phosphor">
            {channel.mhz.toFixed(3)}
            <span className="ml-1 text-base">MHz</span>
          </p>
          <div className="mt-1 flex items-center justify-between">
            <span className="label-etch">{channel.tag}</span>
            <span className="label-etch">{lang.native}</span>
          </div>
          <div className="mt-3 h-6 overflow-hidden rounded border border-etch bg-background">
            <div className="flex h-full items-center gap-[3px] px-2">
              {Array.from({ length: 28 }).map((_, i) => (
                <span
                  key={i}
                  className={`w-[3px] rounded-sm ${live ? "bg-signal" : "bg-etch"}`}
                  style={{
                    height: live ? `${25 + ((i * 37) % 70)}%` : "18%",
                    opacity: live ? 0.5 + ((i * 13) % 50) / 100 : 1,
                  }}
                />
              ))}
            </div>
          </div>
          <p className="mt-3 min-h-10 font-mono text-sm phosphor">
            {interim || (live ? "listening…" : "idle — VAD armed")}
          </p>
        </div>

        {/* channel & language */}
<div className="mt-4 overflow-hidden rounded-2xl border border-etch">

  {/* Header */}
  <button
    onClick={() => setShowSettings((v) => !v)}
    className="flex w-full items-center justify-between px-4 py-3 transition-colors hover:bg-primary/5"
  >
    <span className="label-etch">Channel & Language</span>

    <span className="font-mono text-sm text-primary">
      {showSettings ? "⌃" : "⌄"}
    </span>
  </button>

  {/* Expandable content */}
  {showSettings && (
    <div className="border-t border-etch px-4 pb-4">

      {/* Channel */}
      <div className="mt-4">
        <p className="label-etch mb-2">Channel</p>

        <select
          value={channel.id}
          onChange={(e) => {
            const selected = CHANNELS.find(
              (ch) => ch.id === Number(e.target.value)
            );

            if (selected) setChannel(selected);
          }}
          className="w-full rounded-lg border border-etch bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        >
          {CHANNELS.map((ch) => (
            <option key={ch.id} value={ch.id}>
              {ch.tag} — {ch.mhz.toFixed(3)} MHz
            </option>
          ))}
        </select>
      </div>

      {/* Language */}
      <div className="mt-4">
        <p className="label-etch mb-2">Language</p>

        <select
          value={lang.code}
          onChange={(e) => {
            const selected = LANGUAGES.find(
              (l) => l.code === e.target.value
            );

            if (selected) setLang(selected);
          }}
          className="w-full rounded-lg border border-etch bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
        >
          {LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.native} — {l.name}
            </option>
          ))}
        </select>
      </div>

      {/* Close */}
      <button
        onClick={() => setShowSettings(false)}
        className="mt-4 flex w-full items-center justify-center gap-2 text-xs uppercase tracking-widest text-muted-foreground transition-colors hover:text-primary"
      >
        Close <span className="text-sm">⌃</span>
      </button>

    </div>
  )}
</div>
        {/* PTT dial */}
        <div className="mt-6 flex flex-col items-center">
          <button
            onMouseDown={() => ptt && startTx()}
            onMouseUp={() => ptt && stopTx()}
            onMouseLeave={() => ptt && stopTx()}
            onTouchStart={(e) => {
              e.preventDefault();
              if (ptt) startTx();
            }}
            onTouchEnd={() => ptt && stopTx()}
            className={`flex h-36 w-36 items-center justify-center rounded-full border-2 transition-all ${
              live
                ? "ptt-live border-signal bg-signal/20 text-signal"
                : "border-primary/60 bg-primary/10 text-primary"
            }`}
            aria-label="Hold to speak"
          >
            <Mic className="h-14 w-14" strokeWidth={1.5} />
          </button>
          <p className="mt-3 font-mono text-sm uppercase tracking-widest phosphor">
            {live ? "Transmitting" : ptt ? "Hold to speak" : "Open mic"}
          </p>
          <p className="mt-2 text-center text-xs text-muted-foreground">
            {ptt
              ? "Walkie-talkie mode"
              : "Phone mode"}
          </p>

        </div>

        {/* switches */}
        <div className="mt-5 grid grid-cols-2 gap-2">
          <Toggle
            label="Push to talk"
            on={ptt}
            onClick={() => setPtt((v) => !v)}
          />
          <Toggle
            label="Alert priority"
            on={alertMode}
            danger
            onClick={() => setAlertMode((v) => !v)}
          />
        </div>

        {!supported && (
          <p className="mt-3 text-center text-xs text-signal">
            No on-device recogniser in this browser. On Android the set runs bundled Vosk /
            Whisper-tiny models offline.
          </p>
        )}

        {/* traffic */}
        <div className="mt-5 rounded-2xl border border-etch bg-background/60 p-3">
          <div className="mb-2 flex items-center justify-between">
            <span className="label-etch">Traffic</span>
            <span className="label-etch">
              {latency ? `${latency} ms` : "—"} · {traffic.length} pkt
            </span>
          </div>
          <div className="max-h-56 space-y-2 overflow-y-auto pr-1">
            {traffic.map(({ p, dir }) => (
              <div
                key={p.id + dir}
                className={`rounded-lg border px-3 py-2 ${
                  p.priority === "alert" ? "border-signal/60 bg-signal/10" : "border-etch"
                }`}
              >
                <div className="flex justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  <span className={dir === "TX" ? "text-primary" : "text-accent"}>
                    {dir} · {p.mhz.toFixed(3)}
                  </span>
                  <span>{p.bytes} B</span>
                </div>
                <p className="mt-1 text-sm">{p.text}</p>
              </div>
            ))}
            {traffic.length === 0 && (
              <p className="py-6 text-center text-xs text-muted-foreground">
                CHANNEL CLEAR
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Toggle({
  label,
  on,
  danger,
  onClick,
}: {
  label: string;
  on: boolean;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center justify-between rounded-lg border px-3 py-2 transition-colors ${
        on
          ? danger
            ? "border-signal bg-signal/15"
            : "border-primary bg-primary/15"
          : "border-etch"
      }`}
    >
      <span className="label-etch">{label}</span>
      <span
        className={`h-2.5 w-2.5 rounded-full ${on ? (danger ? "bg-signal" : "bg-primary") : "bg-etch"}`}
      />
    </button>
  );
}
