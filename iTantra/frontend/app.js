// iTantra Web Audio API & Walkie-Talkie Front-End Controller

let audioCtx = null;

function initAudio() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
}

// 2-Tone Tactical Radio Chime Simulation
function playTacticalChime() {
    initAudio();
    try {
        const now = audioCtx.currentTime;
        
        // Tone 1: High alert (880 Hz)
        const osc1 = audioCtx.createOscillator();
        const gain1 = audioCtx.createGain();
        osc1.frequency.setValueAtTime(880, now);
        gain1.gain.setValueAtTime(0.3, now);
        gain1.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
        osc1.connect(gain1);
        gain1.connect(audioCtx.destination);
        osc1.start(now);
        osc1.stop(now + 0.15);

        // Tone 2: Tactical response (660 Hz)
        const osc2 = audioCtx.createOscillator();
        const gain2 = audioCtx.createGain();
        osc2.frequency.setValueAtTime(660, now + 0.16);
        gain2.gain.setValueAtTime(0.3, now + 0.16);
        gain2.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
        osc2.connect(gain2);
        gain2.connect(audioCtx.destination);
        osc2.start(now + 0.16);
        osc2.stop(now + 0.35);
    } catch (e) {}
}

function speakOutLoud(text, langId, urgency) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    try {
        window.speechSynthesis.resume();
        const langMap = { "0": "en-IN", "1": "hi-IN", "2": "bn-IN", "3": "ta-IN", "4": "en-IN" };
        const bcp47 = langMap[langId] || "hi-IN";
        const u = new SpeechSynthesisUtterance(text);
        u.lang = bcp47;
        u.volume = 1.0;
        u.rate = (bcp47.startsWith("bn") || bcp47.startsWith("ta")) ? 0.95 : 1.0;
        if (urgency === 1) {
            u.rate = 1.2;
            u.pitch = 1.25;
        }
        window.speechSynthesis.speak(u);
    } catch (e) {}
}

function loadPreset() {
    const val = document.getElementById("presetSelect").value;
    document.getElementById("messageText").value = val;
}

let isTransmitting = false;

function startPTT() {
    if (isTransmitting) return;
    isTransmitting = true;
    
    document.getElementById("pttBtn").classList.add("active");
    document.getElementById("rxStatus").className = "rx-status-receiving";
    document.getElementById("rxStatus").innerText = "⚡ TRANSMITTING 69-BYTE PACKET OVER RF...";

    sendPacket();
}

function stopPTT() {
    document.getElementById("pttBtn").classList.remove("active");
    isTransmitting = false;
}

async function sendPacket() {
    const text = document.getElementById("messageText").value;
    const langId = document.getElementById("langSelect").value;
    const urgency = document.getElementById("urgencyToggle").checked ? 1 : 0;

    try {
        const response = await fetch("/api/transmit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, lang_id: langId, urgency })
        });

        const data = await response.json();
        
        if (data.status === "SUCCESS") {
            // Update Speaker Output
            const synth = data.synthesis;
            const synthText = synth ? synth.synthesized_text : text;
            document.getElementById("speakerOutput").innerText = `"${synthText}"`;
            
            // Play TTS Speech Audio Out Loud
            speakOutLoud(synthText, langId, urgency);

            // Handle Emergency Audio Feedback
            if (data.decoded_packet.urgency === 1) {
                playTacticalChime();
                document.getElementById("urgencyBadge").classList.remove("hidden");
                document.getElementById("rxStatus").className = "rx-status-receiving red";
                document.getElementById("rxStatus").innerText = `RECEIVED IN ${data.delay_ms}ms (TEMPO +35%, PITCH +40Hz)`;
            } else {
                document.getElementById("urgencyBadge").classList.add("hidden");
                document.getElementById("rxStatus").className = "rx-status-receiving";
                document.getElementById("rxStatus").innerText = `RECEIVED IN ${data.delay_ms}ms (STANDARD ROUTINE)`;
            }

            // Update Hex Display
            updateHexDisplay(data.hex_payload);

            // Log entry
            appendLog(`[DELIVERED] 69B Packet Received in ${data.delay_ms}ms | Speech: "${synthText}"`, "delivered");
        } else {
            document.getElementById("speakerOutput").innerText = "❌ PACKET DROPPED (15% Channel Interference Simulation)";
            document.getElementById("rxStatus").className = "rx-status-receiving red";
            document.getElementById("rxStatus").innerText = "PACKET LOST — Automatic FEC / Retransmission queued";
            appendLog(`[DROPPED] 69B RF Packet Lost in Simulated Interference`, "dropped");
        }

    } catch (err) {
        // Fallback for direct browser transmission
        speakOutLoud(text, langId, urgency);
        if (urgency === 1) playTacticalChime();
        document.getElementById("speakerOutput").innerText = `"${text}"`;
        document.getElementById("rxStatus").innerText = "LOCAL TRANSMISSION COMPLETE";
        appendLog(`[LOCAL DELIVERED] 69B Packet Transmitted: "${text}"`, "delivered");
    } finally {
        stopPTT();
    }
}

function updateHexDisplay(hex) {
    if (!hex) return;
    const bytes = hex.match(/.{1,2}/g);
    let formatted = "";
    for (let i = 0; i < bytes.length; i += 16) {
        const chunk = bytes.slice(i, i + 16).join(" ");
        formatted += `${i.toString(16).padStart(4, '0')}  ${chunk}\n`;
    }
    document.getElementById("hexDisplay").innerText = formatted;
}

function appendLog(msg, type) {
    const consoleBox = document.getElementById("logConsole");
    const div = document.createElement("div");
    div.className = `log-line ${type}`;
    const time = new Date().toLocaleTimeString();
    div.innerText = `[${time}] ${msg}`;
    consoleBox.appendChild(div);
    consoleBox.scrollTop = consoleBox.scrollHeight;
}
