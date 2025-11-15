# Hackathon Iterate - Audio Pipeline 🎙️

Real-time audio pipeline for interview transcription with automatic speaker identification via **LiveKit** (WebRTC) + **ElevenLabs Realtime STT**.

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 3. Generate a LiveKit token
python utils/generate_livekit_token.py

# 4. Run the example
python example_usage.py
```

## ✨ Features

- ✅ LiveKit connection as bot
- ✅ Audio capture from each participant (interviewer + candidate)
- ✅ Audio conversion WebRTC → PCM 16kHz mono
- ✅ ElevenLabs Realtime STT per speaker (no diarization needed)
- ✅ Real-time transcripts with speaker labels
- ✅ Latency < 500ms
- ✅ Error handling and automatic reconnection

## 📦 Architecture

```
LiveKit Room → LiveKitHandler → AudioConverter → ElevenLabs STT → Transcripts
   (WebRTC)      (audio tracks)   (PCM 16kHz)     (WebSocket)    (speaker labels)
```

## 💻 Usage

```python
from audio_pipeline import AudioPipeline

async def main():
    pipeline = AudioPipeline(
        livekit_url="wss://your-server.com",
        livekit_room="interview-room",
        livekit_token="your_token",
        elevenlabs_api_key="your_api_key",
        language="en"
    )

    async for transcript in pipeline.start_transcription():
        print(f"[{transcript.speaker}] {transcript.text}")
```

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Quick start guide (5 min)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture
- **[AUDIO_PIPELINE_README.md](AUDIO_PIPELINE_README.md)** - Complete documentation
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Project structure

## 🎯 Examples

### Simple example
```bash
python example_usage.py
```

### Advanced example (with analysis and storage)
```bash
python advanced_example.py
```

## 🧪 Tests

```bash
pytest test_audio_pipeline.py -v
```

## 📊 Project Structure

```
audio_pipeline/          # Main module
├── pipeline.py          # AudioPipeline (orchestrator)
├── livekit_handler.py   # LiveKit management
├── elevenlabs_stt.py    # ElevenLabs WebSocket client
├── audio_converter.py   # Audio conversion
└── models.py            # Transcript dataclass

docs/                    # Documentation
utils/                   # Utilities (token generator, etc.)
```

## 🔧 Configuration

Required environment variables in `.env`:

```bash
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_TOKEN=your_jwt_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## 🤝 Contributing

Contributions are welcome! See the documentation for more information.

## 📝 License

MIT

---

**Let's cook** 🔥
