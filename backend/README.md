# QuantCoach LiveKit Backend

FastAPI backend for the QuantCoach interview platform with LiveKit video integration and real-time audio transcription.

## Features

- **LiveKit Room Management**: Create and manage interview rooms
- **Token Generation**: Generate secure JWT tokens for participants
- **Real-time Audio Transcription**: Using ElevenLabs STT with batch processing
- **Multi-participant Support**: Interviewer, candidate, and agent roles
- **RESTful API**: Clean endpoints compatible with the QuantCoach frontend

## Architecture

```
backend/
├── server.py                 # FastAPI application with REST endpoints
├── room_manager.py          # LiveKit room and token management
├── transcript_buffer.py     # Buffering system for transcript evaluation
├── audio_pipeline/          # Real-time audio transcription pipeline
│   ├── __init__.py
│   ├── models.py           # Data models (Transcript, BufferedWindow, etc.)
│   ├── pipeline.py         # Main audio pipeline orchestrator
│   ├── livekit_handler.py  # LiveKit connection and audio track management
│   ├── elevenlabs_stt.py   # ElevenLabs STT WebSocket client
│   └── audio_converter.py  # Audio format conversion (48kHz → 16kHz)
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration template
└── example_usage.py       # Example scripts
```

## Setup

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your LiveKit and ElevenLabs credentials:

```env
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### 2. Install Dependencies

Using conda environment (recommended):

```bash
conda activate ttk  # Or your Python environment name
pip install -r requirements.txt
```

### 3. Run the Server

```bash
python server.py
```

The server will start on `http://0.0.0.0:8000`

- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Endpoints

### Health Check

```http
GET /
GET /health
```

Returns server status and LiveKit configuration.

### Create Interview Room

```http
POST /rooms/create
Content-Type: application/json

{
  "room_name": "interview-session-001",  // optional
  "max_participants": 10
}
```

**Response:**
```json
{
  "sid": "RM_xxxxx",
  "name": "interview-session-001",
  "max_participants": 10,
  "creation_time": 1234567890,
  "interviewer_token": "eyJhbGc...",
  "candidate_token": "eyJhbGc...",
  "agent_token": "eyJhbGc...",
  "url": "wss://your-instance.livekit.cloud"
}
```

### Generate Access Token

```http
POST /tokens/generate
Content-Type: application/json

{
  "room_name": "interview-session-001",
  "participant_identity": "user-123",
  "participant_name": "John Doe",
  "role": "interviewer"  // interviewer, candidate, agent, or participant
}
```

**Response:**
```json
{
  "token": "eyJhbGc...",
  "room_name": "interview-session-001",
  "participant_identity": "user-123",
  "url": "wss://your-instance.livekit.cloud"
}
```

### List Active Rooms

```http
GET /rooms
```

### Get Room Participants

```http
GET /rooms/{room_name}/participants
```

### Delete Room

```http
DELETE /rooms/{room_name}
```

## Audio Pipeline

The audio pipeline provides real-time transcription of interview conversations:

### Features

- **Multi-speaker transcription**: Separate streams for interviewer and candidate
- **Real-time processing**: Transcripts appear as participants speak
- **Speaker identification**: Automatic labeling based on participant identity
- **Batch processing**: Optimized 200ms audio chunks for better accuracy
- **Error resilience**: Individual participant failures don't crash the pipeline

### Usage Example

```python
from audio_pipeline import AudioPipeline

pipeline = AudioPipeline(
    livekit_url="wss://your-instance.livekit.cloud",
    livekit_room="interview-session-001",
    livekit_token="agent_token_here",
    elevenlabs_api_key="your_elevenlabs_key",
    language="en"
)

# Start real-time transcription
async for transcript in pipeline.start_transcription():
    print(f"[{transcript.speaker}] {transcript.text}")
    # transcript.is_final indicates if this is the final version
    # transcript.speaker is "recruiter" or "candidate"
```

### Transcript Buffer

The `TranscriptBuffer` class implements a sliding window system for evaluation:

```python
from transcript_buffer import TranscriptBuffer

buffer = TranscriptBuffer(
    window_size_seconds=20.0,
    overlap_seconds=10.0,
    min_transcripts_for_evaluation=2
)

# Add transcripts as they arrive
window = buffer.add_transcript(transcript)
if window:
    # Evaluation window ready (20s of content or speaker turn)
    text = window.get_text(include_speakers=True)
    # Send to LLM for evaluation
```

## Example Scripts

Run the example script to test functionality:

```bash
python example_usage.py
```

This will:
1. Create a test interview room
2. Generate tokens for all participant types
3. List active rooms and participants
4. (Optional) Start real-time transcription

## Frontend Integration

The backend is designed to work seamlessly with the QuantCoach frontend:

1. **Frontend calls** `POST /rooms/create` to create a room
2. **Backend returns** tokens for interviewer, candidate, and agent
3. **Frontend uses** tokens to connect to LiveKit via `@livekit/components-react`
4. **Backend agent** joins room with agent token for transcription
5. **Transcripts** can be sent to frontend via WebSocket or stored in database

## Development

### Project Structure

- `server.py`: Main FastAPI application
- `room_manager.py`: LiveKit room and token management
- `audio_pipeline/`: Real-time transcription system
  - `pipeline.py`: Main orchestrator
  - `livekit_handler.py`: LiveKit connection management
  - `elevenlabs_stt.py`: ElevenLabs WebSocket client
  - `audio_converter.py`: Audio format conversion
  - `models.py`: Data models

### Logging

The backend uses Python's logging module with emoji indicators:

- ✅ Success operations
- ❌ Errors
- ⚠️ Warnings
- 🔌 Connection events
- 🎤 Audio events
- 📋 List operations

### Error Handling

All endpoints include proper error handling with:
- HTTP 503 for LiveKit configuration errors
- HTTP 500 for server errors
- Detailed error messages in responses
- Comprehensive logging for debugging

## Dependencies

Key dependencies:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `livekit` - LiveKit Python SDK
- `livekit-api` - LiveKit API client
- `websockets` - WebSocket client for ElevenLabs
- `numpy` - Audio processing
- `python-dotenv` - Environment configuration

See `requirements.txt` for complete list.

## Troubleshooting

### "LiveKit not configured" error

Make sure your `.env` file contains valid LiveKit credentials:
```env
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret
```

### Audio transcription not working

1. Verify ElevenLabs API key is set in `.env`
2. Check that you have credits in your ElevenLabs account
3. Ensure participants are publishing audio tracks
4. Check logs for WebSocket connection errors

### Module import errors

Make sure you're using the correct Python environment:
```bash
conda activate ttk  # Or your environment name
pip install -r requirements.txt
```

## License

Part of the QuantCoach project.
