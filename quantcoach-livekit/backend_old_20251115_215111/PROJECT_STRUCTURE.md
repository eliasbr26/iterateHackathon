# Audio Pipeline Project Structure

## 📁 File Organization

```
iterateHackathon/
├── 📄 README.md                        # Main project README
├── 📄 AUDIO_PIPELINE_README.md         # Complete pipeline documentation
├── 📄 PROJECT_STRUCTURE.md             # This file
├── 📄 requirements.txt                 # Python dependencies
├── 📄 .env.example                     # Configuration example
│
├── 📂 audio_pipeline/                  # Main module
│   ├── __init__.py                     # Public exports
│   ├── models.py                       # Transcript dataclass
│   ├── pipeline.py                     # AudioPipeline (orchestrator)
│   ├── livekit_handler.py             # LiveKit management
│   ├── elevenlabs_stt.py              # ElevenLabs STT WebSocket client
│   ├── audio_converter.py             # Audio conversion (WebRTC → PCM)
│   ├── error_handling.py              # Error handling and retry
│   └── logging_config.py              # Log configuration
│
├── 📂 docs/                           # Documentation
│   ├── QUICKSTART.md                  # Quick start guide
│   └── ARCHITECTURE.md                # Detailed architecture
│
├── 📂 utils/                          # Utilities
│   ├── __init__.py
│   └── generate_livekit_token.py     # JWT token generator
│
├── 📂 elevenlabs_test/                # ElevenLabs tests (legacy)
│   ├── example.py
│   ├── record_and_transcribe.py
│   └── quazi_real_time_diarized.py
│
├── 📄 example_usage.py                 # Simple example
├── 📄 advanced_example.py              # Advanced example with analysis
└── 📄 test_audio_pipeline.py          # Unit tests
```

## 🎯 Files by Use Case

### To get started quickly
1. **[QUICKSTART.md](docs/QUICKSTART.md)** - Quick start guide
2. **[example_usage.py](example_usage.py)** - Simple example
3. **[requirements.txt](requirements.txt)** - Dependency installation

### To understand the architecture
1. **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Detailed architecture
2. **[AUDIO_PIPELINE_README.md](AUDIO_PIPELINE_README.md)** - Complete documentation
3. **[audio_pipeline/pipeline.py](audio_pipeline/pipeline.py)** - Main code

### For development
1. **[audio_pipeline/](audio_pipeline/)** - All modules
2. **[test_audio_pipeline.py](test_audio_pipeline.py)** - Unit tests
3. **[advanced_example.py](advanced_example.py)** - Advanced example

### For configuration
1. **[.env.example](.env.example)** - Environment variables
2. **[utils/generate_livekit_token.py](utils/generate_livekit_token.py)** - Token generation

## 🔧 Main Modules

### audio_pipeline/pipeline.py
**Main Class**: `AudioPipeline`

The orchestrator that:
- Connects to LiveKit
- Initializes ElevenLabs clients
- Orchestrates audio → transcription flow
- Yields transcripts with speaker labels

**Main Method**:
```python
async def start_transcription(self, audio_stream=None) -> AsyncIterator[Transcript]:
    """Start transcription and yield transcripts"""
```

### audio_pipeline/livekit_handler.py
**Main Class**: `LiveKitHandler`

Manages:
- Connection to LiveKit room
- Participant detection
- Mapping participant → speaker label
- Audio frame streaming

### audio_pipeline/elevenlabs_stt.py
**Main Class**: `ElevenLabsSTT`

Manages:
- WebSocket connection to ElevenLabs
- Audio streaming to API
- Receiving transcripts
- Distinguishing partial/final transcripts

### audio_pipeline/audio_converter.py
**Main Class**: `AudioConverter`

Manages:
- WebRTC → PCM conversion
- Resampling (e.g., 48kHz → 16kHz)
- Multi-channel → mono conversion
- Duration/size calculations

### audio_pipeline/models.py
**Dataclass**: `Transcript`

Data structure for transcripts:
```python
@dataclass
class Transcript:
    text: str
    speaker: str  # "recruiter" or "candidate"
    start_ms: int | None
    end_ms: int | None
    is_final: bool
```

### audio_pipeline/error_handling.py
**Utilities**:
- `retry_async()` - Retry with exponential backoff
- `CircuitBreaker` - Circuit breaker pattern
- `ConnectionHealthMonitor` - Connection monitoring

## 📊 Data Flow

```
LiveKit Room (participants)
    ↓
LiveKitHandler (audio frames)
    ↓
AudioConverter (PCM 16kHz)
    ↓
ElevenLabsSTT (WebSocket)
    ↓
Transcripts with speaker labels
    ↓
AsyncIterator[Transcript]
```

## 🚀 Entry Points

### Simple usage
```bash
python example_usage.py
```

### Advanced usage (with analysis)
```bash
python advanced_example.py
```

### Token generation
```bash
python utils/generate_livekit_token.py
```

### Tests
```bash
pytest test_audio_pipeline.py -v
```

## 📦 Key Dependencies

| Package | Usage |
|---------|-------|
| `livekit` | LiveKit client for WebRTC |
| `livekit-api` | API and token generation |
| `websockets` | WebSocket client for ElevenLabs |
| `numpy` | Audio processing |
| `python-dotenv` | Environment variables |
| `aiohttp` | Async HTTP (fallback) |
| `pytest` | Unit testing |

## 🔐 Required Configuration

Environment variables (`.env`):
```bash
LIVEKIT_URL=wss://your-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_TOKEN=eyJhbGc...
ELEVENLABS_API_KEY=sk_...
```

To generate LiveKit tokens:
```bash
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
```

## 📈 Code Statistics

- **Total Python files**: 15
- **Total lines of code**: ~3000+
- **Main modules**: 7
- **Unit tests**: 12+
- **Documentation**: 4 files

## 🎯 Next Steps

1. ✅ **Installation**: `pip install -r requirements.txt`
2. ✅ **Configuration**: Copy `.env.example` → `.env`
3. ✅ **Token**: `python utils/generate_livekit_token.py`
4. ✅ **Test**: `python example_usage.py`
5. 🚀 **Production**: Integrate into your app

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - 5-minute start
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete architecture
- **[AUDIO_PIPELINE_README.md](AUDIO_PIPELINE_README.md)** - API and usage
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - This file

## 🤝 Contributing

To contribute:
1. Fork the repo
2. Create a feature branch
3. Add tests
4. Submit a PR

## 📝 License

MIT License - See LICENSE file
