# Audio Pipeline - Batch STT 🎙️

Clean, minimal audio transcription pipeline for interviews using **LiveKit** (WebRTC) + **ElevenLabs Batch STT**.

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
- ✅ ElevenLabs Batch STT (5-second windows)
- ✅ Real-time transcripts with speaker labels
- ✅ Simple, clean architecture

## 📦 Architecture

```
LiveKit Room → LiveKitHandler → AudioConverter → Buffer (5s) → ElevenLabs Batch STT → Transcripts
   (WebRTC)      (audio tracks)   (PCM 16kHz)     (buffering)    (REST API)          (speaker labels)
```

## 💻 Usage

```python
from audio_pipeline import AudioPipeline

pipeline = AudioPipeline(
    livekit_url="wss://your-server.com",
    livekit_room="interview-room",
    livekit_token="your_token",
    elevenlabs_api_key="your_key",
    language="en"
)

async for transcript in pipeline.start_transcription():
    print(f"[{transcript.speaker}] {transcript.text}")
```

## 🔧 Configuration

Required environment variables in `.env`:

```bash
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_TOKEN=your_jwt_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

## 📊 Project Structure

```
audio_pipeline/          # Main module
├── pipeline.py          # AudioPipeline (orchestrator)
├── livekit_handler.py   # LiveKit management
├── elevenlabs_stt.py    # ElevenLabs batch STT client
├── audio_converter.py   # Audio conversion
└── models.py            # Transcript dataclass

docs/                    # Documentation
utils/                   # Utilities (token generator, etc.)
```

## ⚙️ How It Works

1. **Connect to LiveKit**: Bot joins room and detects participants
2. **Capture Audio**: LiveKit provides audio tracks for each participant
3. **Convert Format**: WebRTC audio → PCM 16kHz mono
4. **Buffer Audio**: Collect 5 seconds of audio per speaker
5. **Batch Transcribe**: Send buffer to ElevenLabs REST API
6. **Yield Transcripts**: Return transcribed text with speaker label

## 📝 License

MIT

---

**Let's cook** 🔥
