# Audio Pipeline - LiveKit + ElevenLabs Realtime STT

Real-time audio pipeline for interview transcription with speaker separation via LiveKit and ElevenLabs.

## 🎯 Features

- ✅ LiveKit connection as bot
- ✅ Audio track capture from each participant
- ✅ Audio conversion WebRTC → PCM 16kHz mono
- ✅ ElevenLabs Realtime STT connection per speaker
- ✅ Real-time audio streaming
- ✅ Transcripts with speaker labels (recruiter/candidate)
- ✅ Target latency < 500ms
- ✅ Error handling and automatic reconnection

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

Create a `.env` file at the project root:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_TOKEN=your_jwt_token

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### Generating a LiveKit Token

To generate a LiveKit JWT token:

```python
from livekit import api

token = api.AccessToken(api_key, api_secret) \
    .with_identity("bot") \
    .with_name("Transcription Bot") \
    .with_grants(api.VideoGrants(
        room_join=True,
        room="interview-room",
    )).to_jwt()
```

## 🚀 Usage

### Basic Usage

```python
import asyncio
from audio_pipeline import AudioPipeline

async def main():
    pipeline = AudioPipeline(
        livekit_url="wss://your-server.com",
        livekit_room="interview-room",
        livekit_token="your_token",
        elevenlabs_api_key="your_api_key",
        language="en"  # or "fr" for French
    )

    async for transcript in pipeline.start_transcription():
        print(f"[{transcript.speaker}] {transcript.text}")

asyncio.run(main())
```

### Usage with Provided Example

```bash
python example_usage.py
```

## 📊 Project Structure

```
audio_pipeline/
├── __init__.py           # Public exports
├── models.py             # Transcript dataclass
├── livekit_handler.py    # LiveKit management
├── elevenlabs_stt.py     # ElevenLabs WebSocket client
├── audio_converter.py    # Audio conversion
├── pipeline.py           # Main pipeline
└── error_handling.py     # Error handling
```

## 🎤 Architecture

```
┌─────────────┐
│  LiveKit    │
│   Room      │
└──────┬──────┘
       │
       ├─── Participant 1 (Recruiter)
       │    └─── Audio Track
       │         │
       │         ├─► AudioConverter (PCM 16kHz)
       │         │
       │         └─► ElevenLabs STT WebSocket
       │              └─► Transcripts (speaker="recruiter")
       │
       └─── Participant 2 (Candidate)
            └─── Audio Track
                 │
                 ├─► AudioConverter (PCM 16kHz)
                 │
                 └─► ElevenLabs STT WebSocket
                      └─► Transcripts (speaker="candidate")
```

## 📝 API Reference

### Transcript

```python
@dataclass
class Transcript:
    text: str              # Transcribed text
    speaker: str           # "recruiter" or "candidate"
    start_ms: int | None   # Start timestamp (ms)
    end_ms: int | None     # End timestamp (ms)
    is_final: bool         # True if final transcription
```

### AudioPipeline

```python
class AudioPipeline:
    async def start_transcription(
        self,
        audio_stream=None
    ) -> AsyncIterator[Transcript]:
        """
        Start real-time transcription

        Yields:
            Transcript: Transcript objects with speaker labels
        """
```

## ⚙️ Advanced Configuration

### Custom Identities

```python
pipeline = AudioPipeline(
    ...,
    recruiter_identity="john_interviewer",
    candidate_identity="jane_candidate"
)
```

### Language

```python
pipeline = AudioPipeline(
    ...,
    language="fr"  # French
)
```

## 🐛 Debug and Logs

To enable detailed logs:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔍 Troubleshooting

### LiveKit Connection Error

- Verify that the LiveKit URL is correct (wss://)
- Verify that the JWT token is valid and not expired
- Verify that the room exists

### ElevenLabs Error

- Verify that the API key is valid
- Verify that the quota is not exceeded
- Verify the WebSocket connection (firewall, proxy)

### No Transcripts

- Verify that participants have active audio tracks
- Verify that the microphone is authorized
- Check the logs to see if audio is being received

## 📊 Performance

- **Target latency**: < 500ms
- **Audio format**: PCM 16kHz mono 16-bit
- **Audio chunks**: 100ms (configurable)
- **Connections**: 1 ElevenLabs WebSocket per speaker

## 🔐 Security

- Never commit `.env` files
- Use JWT tokens with short expiration
- Regular rotation of API keys
- Validation of participant identities

## 🚧 Current Limitations

- Maximum 2 participants (recruiter + candidate)
- No hot-swapping of participants
- No fallback if ElevenLabs is down
- No transcript caching

## 🔮 Future Improvements

- [ ] Support for more than 2 participants
- [ ] Fallback to Deepgram/Whisper if ElevenLabs fails
- [ ] Transcript caching and persistence
- [ ] Automatic language detection
- [ ] Audio quality metrics
- [ ] Real-time dashboard

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📧 Support

For any questions: [your-email]
