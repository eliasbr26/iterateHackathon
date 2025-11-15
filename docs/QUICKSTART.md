# Quick Start Guide - Batch STT

## Installation (5 minutes)

### 1. Clone and install dependencies

```bash
cd /path/to/iterateHackathon
pip install -r requirements.txt
```

Required dependencies:
- `livekit` - WebRTC audio capture
- `aiohttp` - HTTP client for ElevenLabs
- `numpy` - Audio processing
- `python-dotenv` - Environment variables

### 2. Configuration

Copy the example file and fill it in:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# ElevenLabs Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### 3. Generate a LiveKit token

```bash
python utils/generate_livekit_token.py
```

Copy the bot token into `.env`:

```bash
LIVEKIT_TOKEN=eyJhbGc...
```

## Quick Test (2 minutes)

### Option 1: Test with provided example

```bash
python example_usage.py
```

### Option 2: Test in your code

```python
import asyncio
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

asyncio.run(main())
```

## Complete Workflow

### 1. LiveKit room setup

Two participants must join the room:
- **Interviewer** (identity: `interviewer` or containing `interviewer`)
- **Candidate** (identity: `candidate` or containing `candidate`)

### 2. Launch the transcription bot

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
INFO - [recruiter] Buffering 5000ms per batch request
INFO - [candidate] Buffering 5000ms per batch request

============================================================
REAL-TIME TRANSCRIPTION
============================================================

(waiting 5-6 seconds for first transcript...)

👔 [RECRUITER] ✓ Hello, thank you for joining us today.

(waiting 5-6 seconds...)

👤 [CANDIDATE] ✓ Thank you for having me.

(waiting 5-6 seconds...)

👔 [RECRUITER] ✓ Can you tell me about your experience?

(waiting 5-6 seconds...)

👤 [CANDIDATE] ✓ I have been working in software development for 5 years.
```

**Note**: Transcripts arrive every ~5-6 seconds (batch processing), not continuously.

Legend:
- `✓` : Final transcript (all transcripts are final in batch mode)
- `👔` : Recruiter
- `👤` : Candidate

## What to Expect

### Latency

**~5-6 seconds per transcript**

This is normal for batch STT. The pipeline:
1. Buffers 5 seconds of audio
2. Sends to ElevenLabs (~500ms-1s processing)
3. Returns transcript
4. Repeats

Unlike real-time streaming (~500ms latency), batch processing trades latency for simplicity and compatibility.

### Transcript Format

All transcripts have `is_final=True` - there are no partial updates.

```python
Transcript(
    text="Hello, thank you for joining us.",
    speaker="recruiter",
    is_final=True,  # Always True in batch mode
    start_ms=None,   # Timing info not available
    end_ms=None
)
```

## Configuration Options

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

Trade-off:
- Lower buffer = Lower latency, more API calls, more cost
- Higher buffer = Higher latency, fewer API calls, less cost

## Quick Troubleshooting

### Error: "LIVEKIT_TOKEN not set"

→ Check that `.env` contains `LIVEKIT_TOKEN=...`

### Error: "No participants found"

→ Check that participants have joined the room **before** launching the bot

### No transcripts received

→ Check that:
1. Participants have enabled their microphone
2. The bot has proper permissions: `can_subscribe: true`
3. The logs show "Audio track registered"
4. API key is valid: `ELEVENLABS_API_KEY`

### Error: "ElevenLabs API error (401)"

→ Invalid API key. Check `.env` file.

### Error: "ElevenLabs API error (422)"

→ Invalid audio format. This shouldn't happen with the default setup. Check logs for audio conversion errors.

### Transcripts arrive slowly (> 10 seconds)

→ This is expected with batch STT. Check:
1. Network connection to ElevenLabs
2. Consider reducing `buffer_duration_ms` to 3000

## Next Steps

1. **Integration**: Integrate into your application
2. **Customization**: Adapt speaker labels for your use case
3. **Storage**: Save transcripts to a database
4. **Analysis**: Process transcripts in real-time

## Advanced Usage

### Custom Speaker Mapping

```python
pipeline = AudioPipeline(
    ...,
    recruiter_identity="host",      # Instead of "interviewer"
    candidate_identity="guest"      # Instead of "candidate"
)
```

### Monitoring Transcripts

```python
async for transcript in pipeline.start_transcription():
    # All transcripts are final
    if transcript.speaker == "recruiter":
        print(f"Recruiter said: {transcript.text}")
    else:
        print(f"Candidate said: {transcript.text}")

    # Save to database
    await save_to_db(transcript)

    # Real-time analysis
    sentiment = analyze_sentiment(transcript.text)
    print(f"Sentiment: {sentiment}")
```

## Resources

- [Complete documentation](../AUDIO_PIPELINE_README.md)
- [Detailed architecture](ARCHITECTURE.md)
- [Troubleshooting guide](TROUBLESHOOTING.md)
- [LiveKit Docs](https://docs.livekit.io/)
- [ElevenLabs Docs](https://elevenlabs.io/docs)

## Support

For questions:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [ARCHITECTURE.md](ARCHITECTURE.md)
- LiveKit Documentation
- ElevenLabs Support
