iTantra — Indian Multilingual TTS & STT Neural Transceiver

Smart India Hackathon 2026 — Problem Statement SIH26173
Team: KABOOTAR
Theme: Miscellaneous
Category: Software

📖 Overview

iTantra is an offline-capable, multilingual neural voice transceiver designed for communication over low-bandwidth and unreliable links.

Instead of transmitting raw voice/audio, iTantra converts speech into lightweight text, transfers the text over a constrained communication channel, and reconstructs it as speech at the receiving side.

Core Communication Pipeline

Speech → Speech-to-Text (STT) → Lightweight Text → Transmission → Text → Text-to-Speech (TTS) → Speech

This approach is intended for:

Rural and low-connectivity environments

Disaster and emergency communication

Field operations

Remote communities

Low-bandwidth environments

Situations where mobile data or cloud services are unavailable

Short-range/local communication scenarios

📌 Problem Statement

Voice/audio communication is data-intensive. Over low-data-rate links, transmitting raw audio can require significantly more bandwidth and can become unreliable, especially during:

Disaster and emergency situations

Network outages

Remote/rural operations

Low-bandwidth environments

Field communication

Situations where mobile data or cloud services are unavailable

iTantra addresses this challenge by converting voice into a compact textual representation before transmission.

The result is a communication pipeline that minimizes the amount of information that needs to cross a constrained communication link.

🖥️ Application Preview





🚀 Key Features

1. Speech-to-Text (STT)

Captures a user's voice and converts speech into a text representation before transmission.

2. Text-to-Speech (TTS)

Converts received text back into speech so that the receiver can hear the message naturally.

3. Multilingual Communication

Designed to support communication across Indian and regional languages through multilingual STT and TTS components.

Current supportive languages:

English

Hindi

Bengali

Tamil

4. Low-Bandwidth Communication

Transmits lightweight text rather than raw audio, reducing the amount of data that needs to cross the communication channel.

5. Offline / On-Device AI Capability

The architecture supports local STT/TTS inference, reducing dependency on cloud APIs and continuous internet connectivity when suitable on-device models are available.

6. Device-to-Device Communication

The communication layer is designed to work with locally available connectivity mechanisms such as:

Wi-Fi

Bluetooth

Radio links

Local/LAN communication

7. Walkie-Talkie Style Interaction

The prototype follows a push-to-talk interaction model for short, real-time voice messages.

8. Emergency Communication

Includes an emergency-oriented communication concept with alert-priority functionality for situations where rapid message exchange is important.

9. Network Simulation & Live Metrics

A WebSocket-based simulation layer can be used to evaluate constrained communication conditions and monitor:

Bandwidth

Packet loss

Latency

Bitrate

Word Error Rate (WER)

10. Browser-Based Audio Capture

The frontend uses browser audio capabilities such as the Web Audio API and MediaRecorder API for capturing and playing audio.

🧠 System Workflow

The iTantra communication pipeline follows a Speech → Text → Transmission → Speech architecture.

┌──────────────┐
│   Person A   │
└──────┬───────┘
       │ Speech
       ▼
┌──────────────────────┐
│   Audio Capture      │
│ + Noise Suppression  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Multilingual STT   │
│    Speech → Text     │
└──────────┬───────────┘
           │ Lightweight Text
           ▼
┌──────────────────────┐
│ Compression /        │
│ Encoding / FEC       │
└──────────┬───────────┘
           │
           │ Wi-Fi / Bluetooth /
           │ Radio / WebSocket
           ▼
┌──────────────────────┐
│ Reception +          │
│ Decompression        │
└──────────┬───────────┘
           │ Text
           ▼
┌──────────────────────┐
│   Multilingual TTS   │
│    Text → Speech     │
└──────────┬───────────┘
           │
           ▼
┌──────────────┐
│   Person B   │
└──────────────┘

🏗️ Technical Architecture

The proposed architecture is divided into six major stages.

Stage 1 — Voice Input & Noise Suppression

The browser/client captures the user's voice. Audio preprocessing and voice activity detection can be applied to improve recognition quality.

Stage 2 — Neural Multilingual STT

The speech signal is passed to a multilingual speech-recognition component, which converts the audio into a text representation.

Stage 3 — Compression & Transmission

The recognized text is processed using encoding/compression techniques and may include error-control mechanisms before transmission.

Because text is substantially lighter than raw voice/audio, the communication channel can operate with lower bandwidth requirements.

Stage 4 — Reception & Decompression

The receiver obtains the transmitted data, performs decoding and error recovery where applicable, and reconstructs the text message.

Stage 5 — Audio Reconstruction & Playback

The reconstructed text is passed to the TTS engine, which generates speech for the receiving user.

Stage 6 — Network Simulation & Live Metrics

A WebSocket/communication layer can simulate constrained network conditions and expose live communication metrics for evaluation.

🛠️ Technology Stack

Layer

Technologies / Components

Frontend

HTML, CSS, JavaScript

Backend

Node.js, FastAPI

Transport

WebSocket

Audio

Web Audio API, MediaRecorder API

Edge Inference

ONNX Runtime Web / WebAssembly

ML / Mobile Inference

TensorFlow Lite, PyTorch Mobile

Data / Logging

SQLite, JSON logs

Deployment

Localhost / LAN

Speech Recognition References

AI4Bharat/Vakyansh ASR, whisper.cpp

Speech Synthesis References

AI4Bharat Indic-TTS, sherpa-onnx

Data References

AI4Bharat IndicCorp / IndicVoices, IITM Indic-TTS Dataset

🤖 AI / ML Components

Speech-to-Text

The project references multilingual and offline-capable speech-recognition technologies such as:

AI4Bharat / Vakyansh ASR Toolkit — Indic-language ASR models

whisper.cpp — optimized/offline inference for Whisper models

Text-to-Speech

The project references:

AI4Bharat Indic-TTS — Indic-language TTS models

sherpa-onnx — on-device TTS inference using ONNX-based models

Edge / Offline Inference

Potential inference runtimes include:

ONNX Runtime Web / WebAssembly

TensorFlow Lite

PyTorch Mobile

The overall objective is to move inference closer to the user/device wherever hardware and model size permit.

📡 Low-Bandwidth Communication Strategy

Traditional voice communication sends a continuous audio stream. iTantra instead follows a semantic communication approach:

Raw Speech
    ↓
Speech Recognition
    ↓
Text Representation
    ↓
Compression / Encoding
    ↓
Low-Bandwidth Link
    ↓
Decoding
    ↓
Text
    ↓
Speech Synthesis
    ↓
Reconstructed Voice

This approach is particularly useful when the communication channel has:

Low bitrate

High latency

Packet loss

Intermittent connectivity

Limited data availability

📊 Network & Evaluation Metrics

The prototype can be evaluated at multiple levels.

Speech Recognition

Word Error Rate (WER)

Language-wise accuracy

Noise robustness

Accent/variation robustness

Communication

End-to-end latency

Effective bitrate

Packet-loss tolerance

Reconnection behavior

Speech Reconstruction

TTS quality

Intelligibility

Language correctness

System

CPU usage

Memory consumption

Model size

Battery/resource requirements

Performance on low-end hardware

For multilingual evaluation, metrics should be reported separately for each supported language rather than only as one overall score. This helps identify language-specific performance differences and possible language bias.

🌐 Communication Modes

The architecture is intended to support communication over locally available links such as:

Wi-Fi

Bluetooth

Radio

LAN

WebSocket-based prototype/simulation

The physical radio integration can be treated as a deployment-specific communication layer while the STT → text → TTS pipeline remains modular.

🖥️ Prototype Concept

The prototype UI follows a walkie-talkie-style communication experience and includes concepts such as:

Frequency/channel information

Connection/standby state

Language selection

Push-to-talk control

Voice input

Alert priority

Traffic/status information

Message/communication area

👥 Target Users

iTantra is designed with the following user groups in mind:

Rural and low-connectivity users

Regional-language users

Low-end device users

Emergency and disaster-response teams

Field teams

Students and event teams

Remote communities

Users who cannot depend on continuous internet access

🌍 Expected Impact

Social Impact

Improves communication accessibility in remote communities

Supports regional-language communication

Helps communication during emergencies

Environmental Impact

Reduces dependence on dedicated communication hardware

Makes better use of existing smartphones

Encourages lightweight processing

Economic Impact

Reduces dependency on expensive telecom infrastructure

Works toward low/mid-range device compatibility

Reduces mobile-data requirements

Disaster & Public Safety

Provides an alternative communication channel during network outages

Can help responders exchange critical information

Supports short-range communication without continuous internet dependency

⚠️ Challenges & Mitigation Strategies

Challenge

Proposed Mitigation

Limited CPU / RAM / battery

Quantization and compressed models

STT accuracy affected by accents/noise

Noise filtering and language-specific models

Regional language variation

Multilingual/language-specific speech models

Connectivity interruptions

Reconnection and adaptive switching

Limited Wi-Fi/Bluetooth/radio range

Modular communication layer

Large AI models

Edge optimization and lightweight runtimes

Adding new languages/devices

Modular architecture

🔐 Security & Privacy Considerations

An offline-capable design can reduce the need to send raw voice recordings to cloud services.

Recommended implementation practices:

Keep API keys and credentials outside Git

Use .env files for secrets

Never commit passwords or tokens

Avoid committing private datasets

Validate received communication payloads

Restrict local network access where appropriate

Log only information required for debugging/evaluation

Never upload API keys, passwords, tokens, private certificates, or other secrets to GitHub

📁 Repository Structure

The repository contains the main project components along with supporting files and documentation.

ITANTRA/
├── assets/
│   ├── iTantra_dashboard.png
│   └── iTantra_dashboard2.png
│
├── iTantra/
├── itantra-ai-network/
├── itantrafrontend/
│
├── original_LinkConsole.tsx
├── start_itantra.bat
├── README.md
└── .gitignore

The internal structure of the individual project directories may vary depending on the implementation and development stage.

🚀 Getting Started

1. Clone the Repository

git clone https://github.com/Anubhab47677/ITANTRA.git
cd ITANTRA

2. Review the Project Structure

The repository contains the frontend, AI/network components, project assets and supporting files.

3. Windows Startup

A Windows startup script is included in the repository:

start_itantra.bat

Run the script from the project directory if your local environment has all required dependencies configured.

4. Dependencies

The exact dependencies depend on the implementation used by each project component.

For Node.js-based components, install the dependencies specified by their respective package.json files.

For Python-based components, create and activate a virtual environment and install the dependencies specified by the relevant requirements.txt file if present.

Example:

python -m venv .venv

Then activate the environment and install the required Python packages.

5. Environment Variables

If any component requires environment variables:

.env

should be created locally.

Do not commit .env files, credentials, API keys or other secrets to GitHub.

🧪 Testing & Evaluation

The system can be evaluated using the following dimensions.

Speech Recognition

Word Error Rate (WER)

Language-wise accuracy

Noise robustness

Accent/variation robustness

Communication

End-to-end latency

Effective bitrate

Packet-loss tolerance

Reconnection behavior

Speech Reconstruction

TTS quality

Intelligibility

Language correctness

System Performance

CPU usage

Memory consumption

Model size

Battery/resource requirements

Performance on low-end hardware

Multilingual / Language-Bias Evaluation

Because the current system supports English, Hindi, Bengali and Tamil, evaluation should compare the same metrics independently across all four languages.

A useful evaluation procedure is:

Use comparable test samples for every supported language.

Measure WER and language-wise recognition accuracy separately.

Test speech with different speakers and accents where datasets permit.

Evaluate performance under different noise levels.

Compare latency and resource usage across languages.

Report per-language results instead of hiding differences inside a single average score.

This helps identify whether the model performs substantially better for one language than another.

🔬 Research References

The project references the following technologies and datasets for multilingual speech processing:

AI4Bharat / Vakyansh ASR Toolkit

whisper.cpp

AI4Bharat Indic-TTS

sherpa-onnx

AI4Bharat IndicCorp / IndicVoices

IITM Indic-TTS Dataset

These references support the development and evaluation of multilingual speech-recognition and speech-synthesis components.

🗺️ Future Scope

Potential extensions include:

Adding more Indian languages

Improved language-specific speech recognition

Better noise suppression

Model quantization and pruning

More efficient edge inference

Automatic communication-link selection

Adaptive bitrate/encoding

Real radio-hardware integration

Stronger packet-loss recovery

Expanded emergency-alert functionality

More comprehensive language-wise benchmarking

Improved fairness and language-bias analysis

Support for additional low-resource Indian languages

Broader evaluation across speakers, accents and environments

🏆 Project Context

Project: iTantra
Problem Statement: SIH26173
Event: Smart India Hackathon 2026
Team: KABOOTAR

iTantra aims to combine multilingual speech AI, lightweight text transmission and resilient local communication into a practical communication system for low-bandwidth environments.

👨‍💻 Team

KABOOTAR — Smart India Hackathon 2026

Sovit Swain

Sumana Shyam

Jayita Mandal

Anubhab Samantaray

Akansha Ajay

Ishita Singh

⭐ Support the Project

If you find iTantra useful or interesting, consider starring the repository and sharing feedback or suggestions through GitHub Issues.
