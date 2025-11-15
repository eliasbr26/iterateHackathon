# Quick Start Guide

## Installation (5 minutes)

### 1. Clone and install dependencies

```bash
cd /path/to/iterateHackathon
pip install -r requirements.txt
```

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
INFO - [recruiter] Stream manager started
INFO - [candidate] Stream manager started

============================================================
REAL-TIME TRANSCRIPTION
============================================================

👔 [RECRUITER] ✓ Hello, thank you for joining us today.
👤 [CANDIDATE] ✓ Thank you for having me.
👔 [RECRUITER] ✓ Can you tell me about your experience?
👤 [CANDIDATE] ~ I have been working in software development...
👤 [CANDIDATE] ✓ I have been working in software development for 5 years.
```

Legend:
- `✓` : Final transcript
- `~` : Partial transcript (in progress)
- `👔` : Recruiter
- `👤` : Candidate

## Tests

### Run unit tests

```bash
pytest test_audio_pipeline.py -v
```

### Manual test with test audio

Create a `manual_test.py` file:

```python
import asyncio
from audio_pipeline import AudioPipeline

async def test_with_mock_room():
    """Test with a test room"""
    pipeline = AudioPipeline(
        livekit_url="wss://test.livekit.cloud",
        livekit_room="test-room",
        livekit_token="your_test_token",
        elevenlabs_api_key="your_api_key"
    )

    count = 0
    async for transcript in pipeline.start_transcription():
        print(transcript)
        count += 1

        # Stop after 10 transcripts for testing
        if count >= 10:
            break

    await pipeline.stop()

asyncio.run(test_with_mock_room())
```

## Quick Troubleshooting

### Error: "LIVEKIT_TOKEN not set"

→ Check that `.env` contains `LIVEKIT_TOKEN=...`

### Error: "No participants found"

→ Check that participants have joined the room before launching the bot

### No transcripts

→ Check that:
1. Participants have enabled their microphone
2. The bot has the proper permissions `can_subscribe: true`
3. The logs show "Audio track registered"

### High latency

→ Check:
1. Network connection
2. Reduce audio chunk size (in `pipeline.py`)
3. Use a geographically closer LiveKit server

## Next Steps

1. **Integration**: Integrate into your application
2. **Customization**: Adapt speaker labels
3. **Storage**: Save transcripts to a database
4. **Analytics**: Analyze transcripts in real-time

## Resources

- [Complete documentation](AUDIO_PIPELINE_README.md)
- [Detailed architecture](ARCHITECTURE.md)
- [LiveKit Docs](https://docs.livekit.io/)
- [ElevenLabs Docs](https://elevenlabs.io/docs)

## Support

For any questions:
- GitHub Issues
- LiveKit Documentation
- ElevenLabs Support
