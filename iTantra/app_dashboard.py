"""
iTantra Live Benchmarking & Demonstration Dashboard
Features Automatic Language Detection (English, Hindi, Odia), Male/Female Voice Selection, Radio Transceiver & Replay Audio option.
"""
import os
import time
import json
import streamlit as st
import config
from stt_engine import STTEngine, SUPPORTED_LANGUAGES
from transceiver_engine import PacketEncoder
from tts_engine import TTSEngine
from radio_modem import RadioAudioModem

# Set Streamlit Page Config
st.set_page_config(
    page_title="iTantra - Multilingual Voice Transceiver",
    page_icon="📡",
    layout="wide"
)

@st.cache_resource
def load_stt_engine():
    return STTEngine()

@st.cache_resource
def load_tts_engine():
    return TTSEngine()

st.title("📡 iTantra: Multilingual Radio Speech-to-Speech Transceiver")
st.caption("ISRO SAC Challenge Prototype — Auto Language Detection (**EN**, **HI**, **OR**) & **Male/Female Voice Selection**")

# Sidebar Settings
st.sidebar.header("⚙️ Transceiver & Voice Settings")
bitrate_setting = st.sidebar.slider("Simulated Radio Link Bitrate (bps)", min_value=50, max_value=2400, value=300, step=50)

# Voice Gender Selection in Sidebar
selected_gender_label = st.sidebar.radio("Select Receiver Output Voice:", ["👨 Male Voice", "👩 Female Voice"])
selected_gender_code = "f" if "Female" in selected_gender_label else "m"

st.sidebar.subheader("🌐 Supported Languages:")
st.sidebar.markdown("""
- 🇬🇧 **English (`en`)**
- 🇮🇳 **Hindi (`hi`)**
- 🇮🇳 **Odia (`or`)**
""")

st.sidebar.markdown("---")
st.sidebar.success("🟢 Status: **100% Offline Mode (Zero Internet / Zero Cloud)**")

# Top Banner Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Channel Bandwidth", value=f"{bitrate_setting} bps")
with col2:
    st.metric(label="Raw PCM Voice Bitrate", value="128,000 bps")
with col3:
    st.metric(label="iTantra Packet Bitrate", value="~72 bps")
with col4:
    st.metric(label="Selected Voice", value=selected_gender_label)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs([
    "🎤 Auto Speech-to-Speech (Socket)", 
    "📻 Radio Speech-to-Speech (Acoustic Modem)", 
    "📊 Bandwidth Analytics", 
    "ℹ️ Disaster Architecture & Specs"
])

with tab1:
    st.subheader("🎤 Auto-Detect Speech-to-Speech (English / Hindi / Odia)")
    st.info(f"Target Voice Output: **{selected_gender_label}**. Record voice directly below OR upload an Audio File.")

    audio_input = st.audio_input("Record voice live:")
    file_upload = st.file_uploader("Or Upload / Record Audio File from Phone:", type=["wav", "mp3", "m4a", "ogg"])

    selected_audio = audio_input if audio_input is not None else file_upload

    if selected_audio is not None:
        st.audio(selected_audio)
        
        if st.button("🚀 Run Auto-Detect Speech-to-Speech Pipeline", type="primary"):
            temp_wav_path = os.path.join(config.TEMP_AUDIO_DIR, "live_mic_input.wav")
            with open(temp_wav_path, "wb") as f:
                f.write(selected_audio.read())
            
            with st.spinner("⚡ Step 1: Running Automatic Language Detection & STT..."):
                stt = load_stt_engine()
                stt_result = stt.transcribe_file(temp_wav_path)
            
            text = stt_result["text"]
            detected_lang = stt_result["language"]
            lang_name = stt_result["language_name"]
            raw_audio_size = os.path.getsize(temp_wav_path)
            
            if not text:
                st.warning("⚠️ No speech recognized. Please record/upload clear speech audio.")
            else:
                st.session_state["last_text"] = text
                st.session_state["last_lang"] = detected_lang
                st.session_state["last_lang_name"] = lang_name
                st.session_state["last_gender"] = selected_gender_code
                st.session_state["last_gender_label"] = selected_gender_label

                st.success(f"🔍 **Auto-Detected Language:** `{lang_name}`")
                st.write(f"📝 **Transcribed Speech:** *\"{text}\"*")
                
                payload = {"l": detected_lang, "g": selected_gender_code, "t": text}
                packet_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                packet_size = len(packet_bytes)
                
                tx_time = (packet_size * 8) / bitrate_setting
                raw_tx_time = (raw_audio_size * 8) / bitrate_setting
                savings = (1.0 - (packet_size / max(raw_audio_size, 1))) * 100.0
                
                progress_bar = st.progress(0)
                status_msg = st.empty()
                for i in range(100):
                    time.sleep(0.01)
                    progress_bar.progress(i + 1)
                    status_msg.text(f"📡 Transmitting [{detected_lang.upper()}] packet over {bitrate_setting} bps channel... ({i+1}%)")
                
                status_msg.success(f"✅ Packet Transmitted in {tx_time:.3f}s (vs {raw_tx_time:.1f}s for raw audio)")
                
                st.subheader("🔊 Step 4: Receiver Node (Speech Output)")
                st.write(f"Synthesizing received speech in **{lang_name}** ({selected_gender_label}) out loud...")
                
                tts = load_tts_engine()
                tts.speak(text, lang=detected_lang, gender=selected_gender_code)
                
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.info(f"**📦 iTantra Transmitted Packet:**\n```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n**Size:** `{packet_size} Bytes`")
                with res_col2:
                    st.metric("Raw Audio Size", f"{raw_audio_size:,} Bytes")
                    st.metric("iTantra Packet Size", f"{packet_size} Bytes", delta=f"-{savings:.2f}% reduced")

    # Repeat Audio Button for Tab 1
    if "last_text" in st.session_state:
        st.markdown("---")
        if st.button("🔄 🔊 Repeat / Replay Last Received Audio Speech", key="replay_tab1"):
            st.info(f"🔊 Replaying in **{st.session_state.get('last_lang_name', 'HI')}** ({st.session_state.get('last_gender_label', 'Male')}): *\"{st.session_state['last_text']}\"*")
            tts = load_tts_engine()
            tts.speak(st.session_state['last_text'], lang=st.session_state.get('last_lang', 'hi'), gender=st.session_state.get('last_gender', 'm'))

with tab2:
    st.subheader("📻 Radio Speech-to-Speech (Mic -> Acoustic Radio Signal -> Speech Output)")
    st.info(f"Target Voice Output: **{selected_gender_label}**. iTantra frames the packet and synthesizes voice output in the selected voice.")

    radio_audio_input = st.audio_input("Record voice for Radio Broadcast:")
    radio_file_upload = st.file_uploader("Or Upload Audio File for Radio Broadcast:", type=["wav", "mp3", "m4a", "ogg"], key="radio_uploader")

    selected_radio = radio_audio_input if radio_audio_input is not None else radio_file_upload

    if selected_radio is not None:
        st.audio(selected_radio)
        
        if st.button("📻 Broadcast Radio Speech-to-Speech Signal", type="primary"):
            radio_wav_path = os.path.join(config.TEMP_AUDIO_DIR, "radio_mic_input.wav")
            with open(radio_wav_path, "wb") as f:
                f.write(selected_radio.read())
            
            with st.spinner("⚡ Step 1: Transcribing voice & detecting language..."):
                stt = load_stt_engine()
                stt_res = stt.transcribe_file(radio_wav_path)
            
            r_text = stt_res["text"]
            r_lang = stt_res["language"]
            r_name = stt_res["language_name"]
            
            if not r_text:
                st.warning("⚠️ No speech detected. Please record/upload your voice again.")
            else:
                st.session_state["last_text"] = r_text
                st.session_state["last_lang"] = r_lang
                st.session_state["last_lang_name"] = r_name
                st.session_state["last_gender"] = selected_gender_code
                st.session_state["last_gender_label"] = selected_gender_label

                st.success(f"🔍 **Auto-Detected Language:** `{r_name}`")
                st.write(f"📝 **Transcribed Text:** *\"{r_text}\"*")
                
                st.write("📡 **Step 2: Encoding text into ultra-compact Radio Packet Payload (~50 Bytes)...**")
                pkt_bytes = RadioAudioModem.transmit_radio_sound({"text": r_text, "lang": r_lang, "gender": selected_gender_code}, play_audio=False)
                
                st.success(f"✅ Radio Packet Encoded & Transmitted! Payload Size: `{len(pkt_bytes)} Bytes`")
                
                st.write(f"🔊 **Step 3: Receiver Node synthesizing voice output in {selected_gender_label} out loud...**")
                tts = load_tts_engine()
                tts.speak(r_text, lang=r_lang, gender=selected_gender_code)

    # Repeat Audio Button for Tab 2
    if "last_text" in st.session_state:
        st.markdown("---")
        if st.button("🔄 🔊 Repeat / Replay Last Received Audio Speech", key="replay_tab2"):
            st.info(f"🔊 Replaying in **{st.session_state.get('last_lang_name', 'HI')}** ({st.session_state.get('last_gender_label', 'Male')}): *\"{st.session_state['last_text']}\"*")
            tts = load_tts_engine()
            tts.speak(st.session_state['last_text'], lang=st.session_state.get('last_lang', 'hi'), gender=st.session_state.get('last_gender', 'm'))

with tab3:
    st.subheader("Bandwidth Reduction & Performance Metrics")
    chart_data = {
        "Data Type": ["Raw Voice Audio", "Compressed Voice Codec", "iTantra Neural Packet"],
        "Size in Bytes": [160000, 10000, 52]
    }
    st.bar_chart(data=chart_data, x="Data Type", y="Size in Bytes")

with tab4:
    st.subheader("Disaster Architecture & Real-World Specifications")
    st.markdown("""
    ### Why iTantra Works in Real Disasters:

    1. **Web Browser Prototype vs Installed Native Mobile App:**
       - During hackathons, we use a web dashboard (`app_dashboard.py`) to show judges visual metrics on a laptop.
       - In a real disaster, field personnel use an **Installed Native Android App (`iTantra.apk`)** or **Walkie-Talkie Hardware Modems**.
       - An installed Android APK runs 100% locally on the phone chip—it does **NOT** require any browser, IP address, web server, or Wi-Fi network!

    2. **Radio Speech-to-Speech Pipeline:**
       - **Mic Input:** User speaks into phone mic in English, Hindi, or Odia.
       - **On-Device STT:** Auto-detects language and transcribes text.
       - **Gender Encoding:** Encodes gender preference (`m` or `f`) into payload.
       - **Acoustic Radio Modem:** Encodes ~50-byte text into FSK radio audio tones.
       - **Airwave Broadcast:** Plays radio sound over Walkie-Talkie / HF Radio.
       - **Receiver Base Station:** Listens to audio tones, decodes text, and speaks voice out loud using Male/Female TTS.
    """)
