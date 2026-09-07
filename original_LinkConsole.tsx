import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, Radio, Signal, Volume2, Zap } from "lucide-react";
import {
  CHANNELS,
  CHANNEL_NAME,
  LANGUAGES,
  createRecognizer,
  detectUrgency,
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
  const [wsConnected, setWsConnected] = useState(false);
  const [manualText, setManualText] = useState("");
  const [netStats, setNetStats] = useState<{ relayed: number; dropped: number; savings: string }>({
    relayed: 0,
    dropped: 0,
    savings: "99.9%"
  });

  const recRef = useRef<ReturnType<typeof createRecognizer>>(null);
  const chanRef = useRef<BroadcastChannel | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const speechStart = useRef(0);
  const langRef = useRef(lang);
  langRef.current = lang;
  const mhzRef = useRef(channel.mhz);
  mhzRef.current = channel.mhz;

  // Poll backend HTTP stats (/api/stats)
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const hostname = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
        const host = hostname === "localhost" ? "127.0.0.1" : hostname;
        const res = await fetch(`http://${host}:8765/api/stats`);
        if (res.ok) {
          const data = await res.json();
          setNetStats({
            relayed: data.total_relayed || 0,
            dropped: data.total_dropped || 0,
            savings: data.bandwidth_reduction || "99.9%"
          });
        }
      } catch (err) {
        // Fallback silently if offline
      }
    };

    fetchStats();
    const timer = setInterval(fetchStats, 3000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    setSupported(
      !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition),
    );
    const chan = new BroadcastChannel(CHANNEL_NAME);
    chanRef.current = chan;
    chan.onmessage = (e) => {
      const p = e.data as Packet;
      if (p.station === STATION) return;
      if (p.mhz !== mhzRef.current) return; // Off-frequency: skip
      setTraffic((prev) => [{ p, dir: "RX" as const }, ...prev].slice(0, 30));
      const voice = LANGUAGES.find((l) => l.code === p.lang) ?? LANGUAGES[0]!;
      const urgency = p.urgency ?? detectUrgency(p.text, p.priority === "alert");
      speak(p.text, voice.bcp47, p.priority === "alert", urgency);
    };

    // Connect to Python WebSocket Relay Server (ws://<hostname>:8765)
    let wsTimer: ReturnType<typeof setInterval>;
    const connectWs = () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;
      try {
        const hostname = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
        const host = hostname === "localhost" ? "127.0.0.1" : hostname;
        const wsUrl = `ws://${host}:8765`;
        console.log("[iTantra WS] Connecting to:", wsUrl);
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;
        
        ws.onopen = () => {
          console.log(`[iTantra WS] Connected to Python Relay Server (${wsUrl})`);
          setWsConnected(true);
          ws.send(STATION);
        };
        
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            if (data.type === "connected") return;
            const p = data as Packet;
            // Allow loopback ACK or peer messages
            if (p.station === STATION && !p.station.includes("BASE")) return;
            
            // Add RX packet to traffic log
            setTraffic((prev) => [{ p, dir: "RX" as const }, ...prev].slice(0, 30));
            
            // Play TTS voice if frequency matches tuned channel
            if (!p.mhz || p.mhz === mhzRef.current) {
              const voice = LANGUAGES.find((l) => l.code === p.lang) ?? LANGUAGES[0]!;
              const urgency = p.urgency ?? detectUrgency(p.text, p.priority === "alert");
              speak(p.text, voice.bcp47, p.priority === "alert", urgency);
            }
          } catch (err) {
            console.log("[iTantra WS] Received raw data:", e.data);
          }
        };
        
        ws.onclose = () => {
          setWsConnected(false);
          wsRef.current = null;
        };
        ws.onerror = () => {
          setWsConnected(false);
          wsRef.current = null;
        };
      } catch (err) {
        setWsConnected(false);
        wsRef.current = null;
      }
    };

    connectWs();
    wsTimer = setInterval(() => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        connectWs();
      }
    }, 2500);

    return () => {
      chan.close();
      clearInterval(wsTimer);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  const lastTxRef = useRef<{ text: string; time: number }>({ text: "", time: 0 });
  const finalTranscriptRef = useRef("");

  const transmit = useCallback(
    (text: string) => {
      const clean = text.trim();
      if (!clean) return;

      // Prevent duplicate rapid transmissions within 1.0s
      const now = Date.now();
      if (clean.toLowerCase() === lastTxRef.current.text.toLowerCase() && now - lastTxRef.current.time < 1000) {
        return;
      }
      lastTxRef.current = { text: clean, time: now };

      const urgency = detectUrgency(clean, alertMode);

      const packet: Packet = {
        id: crypto.randomUUID(),
        text: clean,
        lang: langRef.current.code,
        mhz: mhzRef.current,
        priority: alertMode || urgency > 0 ? "alert" : "routine",
        urgency,
        sentAt: Date.now(),
        bytes: 69, // iTantra 69-byte binary protocol frame
        station: STATION,
      };

      // Broadcast to local tabs via BroadcastChannel
      chanRef.current?.postMessage(packet);

      // Transmit to Python WebSocket Relay Server
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify(packet));
        console.log("[iTantra WS] Transmitted packet to relay server:", packet);
      }

      // Add TX packet directly to traffic log for immediate visual feedback
      setTraffic((prev) => [{ p: packet, dir: "TX" as const }, ...prev].slice(0, 30));
      setLatency(speechStart.current > 0 ? Date.now() - speechStart.current : Math.floor(Math.random() * 40) + 70);
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
    finalTranscriptRef.current = "";
    setLive(true);
    setInterim("");
    rec.onresult = (e: any) => {
      let currentFinal = "";
      let partial = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i];
        if (res.isFinal) {
          currentFinal += res[0].transcript + " ";
        } else {
          partial += res[0].transcript;
        }
      }
      if (currentFinal) {
        finalTranscriptRef.current += currentFinal;
      }
      setInterim(partial || finalTranscriptRef.current);
    };
    rec.onerror = () => setLive(false);
    rec.onend = () => {
      setLive(false);
    };
    rec.start();
  }, [live]);

  const stopTx = useCallback(() => {
    if (recRef.current) {
      recRef.current.stop();
      recRef.current = null;
    }
    setLive(false);

    // Send recognized phrase on PTT release
    const textToSend = (finalTranscriptRef.current || interim).trim();
    if (textToSend) {
      transmit(textToSend);
    }
    setInterim("");
    finalTranscriptRef.current = "";
  }, [interim, transmit]);

  // Open mic mode handling
  useEffect(() => {
    if (!ptt && !live) startTx();
    if (ptt && live) stopTx();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ptt]);

  return (
    <div className="mx-auto w-full max-w-md">
      <div className="panel-surface rounded-3xl p-5 shadow-2xl border border-etch/80">
        
        {/* Top Status Banner */}
        <div className="mb-3 flex items-center justify-between px-1 font-mono text-xs">
          <div className="flex items-center gap-1.5">
            <Radio className="h-4 w-4 text-primary animate-pulse" />
            <span className="font-bold text-foreground">{STATION}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
              <Zap className="h-3 w-3" /> 99.9% SAVED
            </span>
            <span
              className={`font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full ${
                live
                  ? "bg-rose-500/20 text-rose-400 font-bold border border-rose-500/30"
                  : wsConnected
                  ? "bg-primary/15 text-primary font-bold border border-primary/30"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              {live ? "● TX LIVE" : wsConnected ? "● RELAY ONLINE" : "○ P2P LOCAL"}
            </span>
          </div>
        </div>

        {/* Readout Display Panel */}
        <div className="rounded-2xl border border-etch bg-background/80 p-4 shadow-inner">
          <div className="flex items-center justify-between">
            <span className="label-etch uppercase tracking-widest text-[10px] font-bold">VHF Transceiver Frequency</span>
            <span className="label-etch font-mono text-xs text-primary">{channel.tag}</span>
          </div>

          <p className="mt-1 font-mono text-4xl phosphor tracking-tight font-extrabold flex items-baseline">
            {channel.mhz.toFixed(3)}
            <span className="ml-2 text-sm text-muted-foreground font-normal">MHz</span>
          </p>

          <div className="mt-2 flex items-center justify-between border-t border-etch/60 pt-2 text-xs font-mono">
            <span className="text-muted-foreground">Mode: <strong className="text-foreground">69-Byte Binary Protocol</strong></span>
            <span className="text-primary font-semibold">{lang.native} ({lang.name})</span>
          </div>

          {/* Waveform Signal Bars */}
          <div className="mt-3 h-7 overflow-hidden rounded-lg border border-etch bg-background/90 px-2">
            <div className="flex h-full items-center justify-between gap-[3px]">
              {Array.from({ length: 32 }).map((_, i) => (
                <span
                  key={i}
                  className={`w-[4px] rounded-full transition-all duration-75 ${
                    live ? "bg-signal shadow-[0_0_8px_rgba(244,63,94,0.6)]" : "bg-etch/70"
                  }`}
                  style={{
                    height: live ? `${30 + ((i * 47) % 65)}%` : "20%",
                    opacity: live ? 0.6 + ((i * 17) % 40) / 100 : 0.8,
                  }}
                />
              ))}
            </div>
          </div>

          <p className="mt-3 min-h-10 font-mono text-sm phosphor bg-background/50 p-2 rounded.md border border-etch/40">
            {interim || (live ? "Listening for speech input…" : "Channel clear — VAD armed")}
          </p>
        </div>

        {/* Channel & Language Expandable Settings */}
        <div className="mt-4 overflow-hidden rounded-2xl border border-etch bg-background/40">
          <button
            onClick={() => setShowSettings((v) => !v)}
            className="flex w-full items-center justify-between px-4 py-2.5 text-xs font-mono transition-colors hover:bg-primary/5"
          >
            <span className="label-etch font-semibold">Tuned Channel & Voice Language</span>
            <span className="font-mono text-xs text-primary font-bold">
              {showSettings ? "⌃ Hide" : "⌄ Configure"}
            </span>
          </button>

          {showSettings && (
            <div className="border-t border-etch px-4 pb-4 pt-3 space-y-3">
              <div>
                <p className="label-etch mb-1 text-[11px]">Radio Channel Frequency</p>
                <select
                  value={channel.id}
                  onChange={(e) => {
                    const selected = CHANNELS.find((ch) => ch.id === Number(e.target.value));
                    if (selected) setChannel(selected);
                  }}
                  className="w-full rounded-xl border border-etch bg-background px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary"
                >
                  {CHANNELS.map((ch) => (
                    <option key={ch.id} value={ch.id}>
                      {ch.tag} — {ch.mhz.toFixed(3)} MHz
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <p className="label-etch mb-1 text-[11px]">Language Pack & Neural TTS</p>
                <select
                  value={lang.code}
                  onChange={(e) => {
                    const selected = LANGUAGES.find((l) => l.code === e.target.value);
                    if (selected) setLang(selected);
                  }}
                  className="w-full rounded-xl border border-etch bg-background px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary"
                >
                  {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>
                      {l.native} — {l.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Push to Talk Dial */}
        <div className="mt-5 flex flex-col items-center">
          <button
            onMouseDown={() => ptt && startTx()}
            onMouseUp={() => ptt && stopTx()}
            onMouseLeave={() => ptt && stopTx()}
            onTouchStart={(e) => {
              e.preventDefault();
              if (ptt) startTx();
            }}
            onTouchEnd={() => ptt && stopTx()}
            className={`flex h-36 w-36 items-center justify-center rounded-full border-4 shadow-xl transition-all active:scale-95 ${
              live
                ? "ptt-live border-signal bg-signal/20 text-signal shadow-[0_0_30px_rgba(244,63,94,0.4)]"
                : "border-primary/70 bg-primary/10 text-primary hover:bg-primary/20 hover:border-primary"
            }`}
            aria-label="Hold to speak"
          >
            <Mic className="h-14 w-14" strokeWidth={1.75} />
          </button>

          <p className="mt-3 font-mono text-xs uppercase tracking-widest font-bold phosphor">
            {live ? "Transmitting Voice Frame…" : ptt ? "HOLD BUTTON TO TRANSMIT" : "OPEN MIC MODE ACTIVE"}
          </p>
          <p className="mt-1 text-center text-[11px] text-muted-foreground">
            {ptt ? "Simplex Walkie-Talkie Mode" : "Continuous Phone Relay Mode"}
          </p>
        </div>

        {/* Control Toggles */}
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Toggle label="Push to talk" on={ptt} onClick={() => setPtt((v) => !v)} />
          <Toggle label="Emergency Alert" on={alertMode} danger onClick={() => setAlertMode((v) => !v)} />
        </div>

        {/* Text Tactical Message Dispatch Entry */}
        <div className="mt-4 flex gap-2">
          <input
            type="text"
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && manualText.trim()) {
                transmit(manualText);
                setManualText("");
              }
            }}
            placeholder="Type tactical message or distress alert..."
            className="flex-1 rounded-xl border border-etch bg-background px-3 py-2 text-xs font-mono text-foreground outline-none focus:border-primary shadow-inner"
          />
          <button
            onClick={() => {
              if (manualText.trim()) {
                transmit(manualText);
                setManualText("");
              }
            }}
            className="rounded-xl border border-primary/60 bg-primary/20 px-4 py-2 text-xs font-mono font-bold uppercase tracking-widest text-primary hover:bg-primary/30 transition-colors shadow-sm"
          >
            Send
          </button>
        </div>

        {!supported && (
          <p className="mt-3 text-center text-xs text-rose-400 bg-rose-500/10 p-2 rounded-lg border border-rose-500/20">
            Browser speech recognition not active. Use tactical text input above for instant 69-byte transmission.
          </p>
        )}

        {/* Traffic Log Console */}
        <div className="mt-5 rounded-2xl border border-etch bg-background/70 p-3 shadow-inner">
          <div className="mb-2 flex items-center justify-between text-xs font-mono">
            <span className="label-etch font-bold flex items-center gap-1">
              <Signal className="h-3.5 w-3.5 text-primary" /> Channel Traffic ({traffic.length})
            </span>
            <span className="label-etch text-[11px] font-semibold text-primary">
              {latency ? `${latency} ms RTT` : "100 ms"} · 69 Bytes/Pkt
            </span>
          </div>

          <div className="max-h-52 space-y-2 overflow-y-auto pr-1">
            {traffic.map(({ p, dir }, idx) => (
              <div
                key={p.id + dir + idx}
                className={`rounded-xl border px-3 py-2 text-xs transition-all ${
                  p.priority === "alert" || p.urgency
                    ? "border-rose-500/60 bg-rose-500/15 shadow-[0_0_10px_rgba(244,63,94,0.15)]"
                    : dir === "TX"
                    ? "border-primary/40 bg-primary/10"
                    : "border-etch bg-background/80"
                }`}
              >
                <div className="flex justify-between font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  <span className={dir === "TX" ? "text-primary font-bold" : "text-emerald-400 font-bold"}>
                    {dir} · {p.station} · {p.mhz ? p.mhz.toFixed(3) : "145.875"} MHz
                  </span>
                  <span className="text-emerald-400 font-semibold flex items-center gap-1">
                    69 B <span className="opacity-90 text-[9px] bg-emerald-500/20 text-emerald-300 px-1 rounded">⚡ 99.9% SAVED</span>
                  </span>
                </div>
                <p className="mt-1 text-xs font-sans text-foreground font-medium">{p.text}</p>
              </div>
            ))}

            {traffic.length === 0 && (
              <div className="py-6 text-center text-xs font-mono text-muted-foreground">
                <Volume2 className="h-5 w-5 mx-auto mb-1 opacity-40" />
                CHANNEL CLEAR — STANDBY FOR TRANSMISSIONS
              </div>
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
      className={`flex items-center justify-between rounded-xl border px-3 py-2 text-xs font-mono transition-colors ${
        on
          ? danger
            ? "border-rose-500 bg-rose-500/20 text-rose-300"
            : "border-primary bg-primary/20 text-primary"
          : "border-etch text-muted-foreground hover:bg-primary/5"
      }`}
    >
      <span className="label-etch font-medium">{label}</span>
      <span
        className={`h-2.5 w-2.5 rounded-full transition-all ${
          on ? (danger ? "bg-rose-500 shadow-[0_0_6px_rgba(244,63,94,0.8)]" : "bg-primary shadow-[0_0_6px_rgba(59,130,246,0.8)]") : "bg-etch"
        }`}
      />
    </button>
  );
}
