# Audio Pipeline - LiveKit + ElevenLabs Batch STT

Clean audio pipeline for interview transcription with speaker separation using **LiveKit** (WebRTC) and **ElevenLabs Batch STT** (REST API).

## 🎯 Features

- ✅ LiveKit connection as bot
- ✅ Audio track capture from each participant
- ✅ Audio conversion WebRTC → PCM 16kHz mono
- ✅ ElevenLabs Batch STT via REST API
- ✅ 5-second audio buffering per speaker
- ✅ Transcripts with speaker labels (recruiter/candidate)
- ✅ Latency: ~5-6 seconds per transcript
- ✅ Simple HTTP-based architecture (no WebSockets)
- ✅ All transcripts are final (no partial updates)

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

Required dependencies:
- `livekit>=0.11.0` - WebRTC audio capture
- `aiohttp>=3.9.0` - HTTP client for ElevenLabs
- `numpy>=1.24.0` - Audio processing
- `python-dotenv>=1.0.0` - Environment variables

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

Use the provided utility:

```bash
python utils/generate_livekit_token.py
```

Or generate manually:

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
        # All transcripts are final (is_final=True)
        print(f"[{transcript.speaker}] {transcript.text}")

asyncio.run(main())
```

### Usage with Provided Example

```bash
python example_usage.py
```

Expected output:

```
INFO - Starting audio pipeline...
INFO - Connecting to LiveKit room: interview-room
INFO - Connected to LiveKit room
INFO - Waiting for participants...
INFO - Found 2 participants
INFO - [recruiter] Stream manager started (batch mode)
INFO - [candidate] Stream manager started (batch mode)

============================================================
REAL-TIME TRANSCRIPTION
============================================================

(waiting 5-6 seconds for first transcript...)

👔 [RECRUITER] ✓ Hello, thank you for joining us today.

(waiting 5-6 seconds...)

👤 [CANDIDATE] ✓ Thank you for having me.
```

**Note**: Transcripts arrive every ~5-6 seconds due to batch processing.

## 📊 Project Structure

```
audio_pipeline/
├── __init__.py           # Public exports
├── models.py             # Transcript dataclass
├── livekit_handler.py    # LiveKit connection management
├── elevenlabs_stt.py     # ElevenLabs batch STT client (REST API)
├── audio_converter.py    # Audio format conversion
├── pipeline.py           # Main pipeline with buffering logic
└── logging_config.py     # Logging configuration
```

## 🎤 Architecture

### High-Level Flow

```
┌─────────────┐
│  LiveKit    │
│   Room      │
└──────┬──────┘
       │
       ├─── Participant 1 (Recruiter)
       │    └─── Audio Track
       │         │
       │         ├─► AudioConverter (WebRTC → PCM 16kHz)
       │         │
       │         ├─► Buffer (5 seconds)
       │         │
       │         └─► ElevenLabs Batch STT (HTTP POST)
       │              └─► Transcript (speaker="recruiter")
       │
       └─── Participant 2 (Candidate)
            └─── Audio Track
                 │
                 ├─► AudioConverter (WebRTC → PCM 16kHz)
                 │
                 ├─► Buffer (5 seconds)
                 │
                 └─► ElevenLabs Batch STT (HTTP POST)
                      └─► Transcript (speaker="candidate")
```

### Detailed Processing Pipeline

```
Step 1: LiveKit Audio Capture
   ↓ Audio frames from WebRTC track
Step 2: Audio Conversion
   ↓ Convert to PCM 16kHz mono 16-bit
Step 3: Buffer Accumulation
   ↓ Accumulate 5 seconds of audio (80,000 bytes)
Step 4: WAV Conversion
   ↓ Wrap PCM in WAV format (add 44-byte RIFF header)
Step 5: HTTP POST Request
   ↓ Send to: https://api.elevenlabs.io/v1/speech-to-text
Step 6: Transcript Response
   ↓ Receive JSON: {"text": "transcribed text"}
Step 7: Queue & Yield
   ↓ Add speaker label and yield to user
```

## 📝 API Reference

### Transcript

```python
@dataclass
class Transcript:
    text: str              # Transcribed text
    speaker: str           # "recruiter" or "candidate"
    start_ms: int | None   # Start timestamp (not available in batch mode)
    end_ms: int | None     # End timestamp (not available in batch mode)
    is_final: bool         # Always True in batch mode
```

### AudioPipeline

```python
class AudioPipeline:
    def __init__(
        self,
        livekit_url: str,
        livekit_room: str,
        livekit_token: str,
        elevenlabs_api_key: str,
        language: str = "en",
        recruiter_identity: str = "interviewer",
        candidate_identity: str = "candidate",
        buffer_duration_ms: int = 5000  # 5 seconds (configurable)
    ):
        """
        Initialize the audio pipeline

        Args:
            livekit_url: LiveKit server URL (wss://...)
            livekit_room: Room name
            livekit_token: JWT token for bot
            elevenlabs_api_key: ElevenLabs API key
            language: Language code (en, fr, es, etc.)
            recruiter_identity: Identity substring for recruiter
            candidate_identity: Identity substring for candidate
            buffer_duration_ms: Audio buffer duration in milliseconds
        """

    async def start_transcription(self) -> AsyncIterator[Transcript]:
        """
        Start batch transcription

        Yields:
            Transcript: Final transcript objects every ~5-6 seconds
        """
```

### ElevenLabsSTT

```python
class ElevenLabsSTT:
    async def transcribe_pcm(
        self,
        audio_pcm: bytes,
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe PCM audio using ElevenLabs batch STT

        Args:
            audio_pcm: Raw PCM audio bytes (16-bit mono)
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text (empty string if no speech detected)
        """
```

## ⚙️ Advanced Configuration

### Adjust Buffer Duration

For lower latency (more API calls):

```python
pipeline = AudioPipeline(
    ...,
    buffer_duration_ms=3000  # 3 seconds instead of 5
)
```

For higher latency (fewer API calls):

```python
pipeline = AudioPipeline(
    ...,
    buffer_duration_ms=10000  # 10 seconds
)
```

**Trade-off:**
- Lower buffer = Lower latency, more API calls, higher cost
- Higher buffer = Higher latency, fewer API calls, lower cost

### Custom Speaker Identities

```python
pipeline = AudioPipeline(
    ...,
    recruiter_identity="host",      # Match "host" in LiveKit identity
    candidate_identity="guest"      # Match "guest" in LiveKit identity
)
```

### Language Configuration

```python
pipeline = AudioPipeline(
    ...,
    language="fr"  # French, Spanish, etc.
)
```

Supported languages: `en`, `fr`, `es`, `de`, `it`, `pt`, and others supported by ElevenLabs.

## 🐛 Debug and Logs

To enable detailed logs:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Or use colored logging (if available):

```python
from audio_pipeline import setup_colored_logging

setup_colored_logging(level=logging.DEBUG)
```

## 🔍 Troubleshooting

### LiveKit Connection Error

- Verify that the LiveKit URL is correct (wss://)
- Verify that the JWT token is valid and not expired
- Verify that the room exists and bot has `can_subscribe: true` permission

### ElevenLabs API Error (401 Unauthorized)

- Verify that the API key is valid: `ELEVENLABS_API_KEY`
- Check your ElevenLabs account status
- Ensure API key has not been revoked

### ElevenLabs API Error (422 Unprocessable Entity)

- Invalid audio format sent to API
- Check logs for audio conversion errors
- This should not happen with default setup

### No Transcripts Received

Check that:
1. Participants have joined the room **before** launching the bot
2. Participants have enabled their microphone
3. Bot has proper permissions: `can_subscribe: true`
4. Logs show "Audio track registered" for each participant
5. Logs show "Stream manager started (batch mode)"

### Transcripts Arrive Slowly (> 10 seconds)

This is expected with batch STT. Each transcript requires:
1. Buffering 5 seconds of audio locally
2. Sending HTTP POST to ElevenLabs (~500ms-1s)
3. Processing and receiving response

Total: ~5-6 seconds per transcript

To reduce latency, decrease `buffer_duration_ms`:

```python
pipeline = AudioPipeline(..., buffer_duration_ms=3000)
```

### Empty Transcripts / No Speech Detected

- Verify audio is being captured (check LiveKit room)
- Increase microphone volume
- Ensure participants are speaking clearly
- Check for background noise or audio quality issues

## 📊 Performance

- **Latency**: ~5-6 seconds per transcript
- **Audio format**: PCM 16kHz mono 16-bit
- **Buffer size**: 5 seconds (80,000 bytes) by default
- **API calls**: 1 HTTP POST per buffer (every 5 seconds per speaker)
- **Connections**: 1 HTTP session per ElevenLabsSTT client (connection pooling enabled)

### Latency Breakdown

```
Audio buffering:    5000ms  (configurable)
Network + API:       500ms  (ElevenLabs processing)
Queue processing:     50ms  (internal)
--------------------------------
Total:             ~5550ms  (~5.6 seconds)
```

## 🔐 Security

- Never commit `.env` files to version control
- Use JWT tokens with short expiration (< 24 hours)
- Regular rotation of API keys
- Validate participant identities before processing
- Use secure WebSocket connections (wss://)

## 🚧 Current Limitations

### By Design (Batch Processing)

- **Higher latency**: ~5-6 seconds per transcript (vs ~500ms for streaming)
- **No partial transcripts**: Only final results are returned
- **Fixed buffer windows**: Audio is processed in discrete 5-second chunks
- **No overlap**: Sentences split across buffers may be transcribed separately

### Implementation Limits

- **Maximum 2 participants**: Designed for recruiter + candidate only
- **No hot-swapping**: Participants must join before bot starts
- **No fallback STT**: If ElevenLabs fails, transcription stops
- **No transcript persistence**: Transcripts are only yielded, not stored

## 💡 How Buffering Works

### Buffer Accumulation

```
Time:    0s      1s      2s      3s      4s      5s
Audio:   [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓]
         │                              │
         └─ Start buffering             └─ Send to API
                                           Reset buffer
```

### Continuous Processing

```
Buffer 1: [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] → API → "Hello, thank you for joining."
Buffer 2: [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] → API → "Can you tell me about yourself?"
Buffer 3: [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] → API → "I have five years of experience."
```

Each buffer:
- Accumulates exactly 5 seconds of audio (configurable)
- Converts PCM → WAV format
- Sends via HTTP POST to ElevenLabs
- Receives final transcript text
- Queues transcript with speaker label

## 🎯 Use Cases

### Best For

✅ Interview transcription with known participants
✅ Scenarios where 5-6 second latency is acceptable
✅ Simple deployment without WebSocket complexity
✅ Standard ElevenLabs API access (no enterprise features needed)
✅ Reliable, predictable transcription

### Not Ideal For

❌ Real-time interactive conversations requiring < 1s latency
❌ Live captioning or subtitles
❌ Voice assistants or chatbots
❌ More than 2 speakers
❌ Dynamic participant joining/leaving

## 🔮 Future Improvements

Possible enhancements (not currently implemented):

- [ ] Support for > 2 participants with dynamic speaker detection
- [ ] Fallback to Deepgram/Whisper if ElevenLabs fails
- [ ] Transcript caching and database persistence
- [ ] Automatic language detection per speaker
- [ ] Audio quality metrics and monitoring
- [ ] Real-time dashboard for monitoring transcription
- [ ] Overlap buffering to prevent sentence splitting
- [ ] Adaptive buffer sizing based on speech detection
- [ ] Resume/reconnection logic for interrupted sessions

## 📚 Additional Documentation

- [Quick Start Guide](docs/QUICKSTART.md) - Get started in 5 minutes
- [Architecture Details](docs/ARCHITECTURE.md) - Deep dive into components
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Visual Guide](docs/VISUAL_GUIDE.md) - Diagrams and visualizations

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! When contributing:

1. Maintain the clean, simple architecture
2. Avoid adding streaming/WebSocket complexity
3. Follow existing code style
4. Add tests for new features
5. Update documentation

## 📧 Support

For questions and issues:
- Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- Review [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Open an issue on GitHub
- Consult [LiveKit Documentation](https://docs.livekit.io/)
- Consult [ElevenLabs Documentation](https://elevenlabs.io/docs)

---

**Version**: 2.0.0
**Architecture**: Batch STT (REST API)
**Last Updated**: 2025-11-15
