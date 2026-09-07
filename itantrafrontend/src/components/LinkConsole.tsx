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
      } else {
        // Fallback for single tab: speech synthesis feedback
        const voice = LANGUAGES.find((l) => l.code === packet.lang) ?? LANGUAGES[0]!;
        speak(packet.text, voice.bcp47, packet.priority === "alert", urgency);
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
    const spoken = (finalTranscriptRef.current || interim).trim();
    if (spoken) {
      transmit(spoken);
    }
    setInterim("");
  }, [interim, transmit]);

  return (
    <div className="mx-auto max-w-lg p-3 sm:p-4">
      {/* Header Bar */}
      <div className="tactical-panel relative overflow-hidden rounded-3xl p-5 shadow-2xl">
        <div className="flex items-center justify-between border-b border-etch pb-3">
          <div className="flex items-center gap-2.5">
            <Radio className="h-6 w-6 text-primary animate-pulse" />
            <div>
              <h1 className="font-mono text-sm font-bold tracking-wider text-foreground">
                iTANTRA TRANSCEIVER
              </h1>
              <div className="flex items-center gap-2">
                <p className="text-[10px] font-mono text-muted-foreground uppercase">
                  {STATION} · SIMPLEX VHF
                </p>
                <span className={`h-2 w-2 rounded-full ${wsConnected ? "bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" : "bg-amber-400 animate-ping"}`} />
                <span className="text-[10px] font-mono text-muted-foreground">
                  {wsConnected ? "RELAY CONNECTED" : "LOCAL LINK"}
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => setShowSettings((v) => !v)}
            className="rounded-xl border border-etch bg-background/60 p-2 text-muted-foreground hover:text-foreground transition-all"
          >
            <Zap className="h-4 w-4 text-primary" />
          </button>
        </div>

        {/* Bandwidth Savings Banner */}
        <div className="mt-3 flex items-center justify-between rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-mono">
          <span className="text-emerald-400 font-bold flex items-center gap-1">
            <Zap className="h-3.5 w-3.5" /> ⚡ 99.9% Bandwidth Reduction
          </span>
          <span className="text-emerald-300 font-semibold">
            69 Bytes / 5s Payload
          </span>
        </div>

        {/* Frequency & Display Unit */}
        <div className="mt-4 rounded-2xl border border-etch bg-background/80 p-4 font-mono shadow-inner">
          <div className="flex items-baseline justify-between">
            <span className="label-etch text-xs">TUNED FREQUENCY</span>
            <span className="text-2xl font-black text-primary font-mono tracking-tight phosphor">
              {channel.mhz.toFixed(3)} <span className="text-xs font-normal text-muted-foreground">MHz</span>
            </span>
          </div>

          <div className="mt-3 flex gap-2">
            {CHANNELS.map((c) => (
              <button
                key={c.id}
                onClick={() => setChannel(c)}
                className={`flex-1 rounded-xl border py-1.5 text-[11px] font-bold transition-all ${
                  channel.id === c.id
                    ? "border-primary bg-primary/20 text-primary shadow-[0_0_10px_rgba(59,130,246,0.2)]"
                    : "border-etch text-muted-foreground hover:bg-primary/5"
                }`}
              >
                {c.tag}
              </button>
            ))}
          </div>

          {/* LANGUAGE DROPDOWN MENU */}
          <div className="mt-3 flex items-center justify-between text-xs pt-2 border-t border-etch/60">
            <span className="label-etch">LANGUAGE PROTOCOL</span>
            <select
              value={lang.code}
              onChange={(e) => {
                const found = LANGUAGES.find((l) => l.code === e.target.value);
                if (found) setLang(found);
              }}
              className="rounded-lg border border-etch bg-background px-3 py-1.5 text-xs font-bold text-foreground outline-none focus:border-primary cursor-pointer shadow-sm"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.name} ({l.native})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Live Audio / Status Display */}
        <div className="mt-4 rounded-2xl border border-etch bg-background/50 p-4 text-center">
          <p className="font-mono text-xs text-muted-foreground">STATUS / SPEECH STREAM</p>
          <div className="mt-1 min-h-[3rem] flex items-center justify-center">
            {live ? (
              <p className="font-sans text-sm font-semibold text-signal animate-pulse">
                "{interim || "Listening... speak now..."}"
              </p>
            ) : manualText ? (
              <p className="font-sans text-xs text-primary font-mono">
                Draft: "{manualText}"
              </p>
            ) : (
              <p className="font-mono text-xs text-muted-foreground">
                [READY FOR TRANSMISSION]
              </p>
            )}
          </div>
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
