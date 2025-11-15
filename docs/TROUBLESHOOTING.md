
### 1. Connection Errors

#### ❌ "LIVEKIT_TOKEN not set in environment"

**Cause**: Environment variable missing

**Solutions**:
```bash
# Check that .env exists
ls -la .env

# Check the content
cat .env | grep LIVEKIT_TOKEN

# If missing, generate a token
python utils/generate_livekit_token.py
```

#### ❌ "Failed to connect to LiveKit"

**Possible causes**:
1. Incorrect URL
2. Expired or invalid token
3. Network/firewall issue
4. Room does not exist

**Solutions**:
```bash
# 1. Check the URL
echo $LIVEKIT_URL
# Must be in format: wss://your-server.com

# 2. Generate a new token
python utils/generate_livekit_token.py

# 3. Test the connection
curl -I https://your-livekit-server.com

# 4. Check detailed logs
LOG_LEVEL=DEBUG python example_usage.py
```

#### ❌ "ElevenLabs API error (401): Unauthorized"

**Cause**: Invalid or missing API key

**Solutions**:
```bash
# 1. Check the API key
echo $ELEVENLABS_API_KEY

# 2. Test the API key manually
curl -H "xi-api-key: $ELEVENLABS_API_KEY" \
  https://api.elevenlabs.io/v1/user

# 3. Verify key is active in ElevenLabs dashboard
# Go to: https://elevenlabs.io/app/settings/api-keys
```

#### ❌ "ElevenLabs API error (422): Invalid audio format"

**Cause**: Audio format not compatible with ElevenLabs

**Solutions**:
1. Check audio conversion logs
2. Verify PCM format is correct (16kHz, mono, 16-bit)
3. Enable debug logging to see conversion details:

```python
import logging
logging.getLogger("audio_pipeline.audio_converter").setLevel(logging.DEBUG)
```

### 2. Participant Issues

#### ❌ "Only 0 participant(s) found. Expected at least 2"

**Cause**: Participants haven't joined the room before bot

**Solutions**:
1. **Have participants join BEFORE launching the bot**
2. Increase the wait timeout (in `pipeline.py`, line ~266):
   ```python
   max_wait = 60  # Increase from 30 to 60 seconds
   ```

#### ❌ "Participant [identity] not found"

**Cause**: Incorrect identity or participant disconnected

**Solutions**:
```bash
# Check participant identities in logs
LOG_LEVEL=DEBUG python example_usage.py

# Expected output:
# INFO - Participant connected: interviewer
# INFO - Participant connected: candidate
```

### 3. Audio Issues

#### ❌ "Audio track not available after 30s"

**Possible causes**:
1. Participant hasn't enabled their microphone
2. Permissions denied
3. Track not published

**Solutions**:
```bash
# 1. Check in the logs
grep "Audio track" logs.txt

# 2. Check that can_subscribe=True in the token
python utils/generate_livekit_token.py

# 3. Test with a test participant
# Use the LiveKit web interface to test
```

#### ❌ "Error converting audio frame"

**Possible causes**:
1. Incompatible audio format
2. Corrupted frame
3. Unsupported sample rate

**Solutions**:
```python
# Enable detailed conversion logs
import logging
logging.getLogger("audio_pipeline.audio_converter").setLevel(logging.DEBUG)

# Check frame format in logs
# Expected: 16kHz or 48kHz, mono or stereo, int16
```

### 4. Transcription Issues

#### ❌ "No transcripts received"

**Possible causes**:
1. No audio being sent
2. ElevenLabs not detecting speech
3. Invalid API key
4. Incorrect language
5. Network issues

**Solutions**:
```python
# 1. Check that audio is being sent
# Logs to look for:
# "[speaker] Sending X bytes to batch STT"

# 2. Check the language
pipeline = AudioPipeline(
    ...,
    language="en"  # Or "fr", "es", etc.
)

# 3. Test with known audio content
# Have someone speak clearly for 5+ seconds

# 4. Check ElevenLabs logs
grep "ElevenLabs" logs.txt | grep -i error

# 5. Verify network connectivity
curl -I https://api.elevenlabs.io
```

#### ❌ "Transcripts arrive very slowly (> 10 seconds)"

**Cause**: This is expected behavior for batch STT

**Explanation**:
- Batch STT buffers 5 seconds of audio
- Sends to ElevenLabs (~500ms-1s processing)
- Total: ~5-6 seconds per transcript

This is **normal** and significantly slower than real-time streaming (~500ms).

**Solutions to reduce latency**:
```python
# 1. Reduce buffer duration (more API calls)
pipeline = AudioPipeline(
    ...,
    buffer_duration_ms=3000  # 3 seconds instead of 5
)

# 2. Check network latency
ping api.elevenlabs.io

# 3. Use a closer geographic region for LiveKit
```

#### ❌ "Empty transcripts / No speech detected"

**Cause**: ElevenLabs returned empty string (no speech in buffer)

**Explanation**: If a 5-second buffer contains only silence or unclear audio, ElevenLabs returns no text. This is normal.

**Solutions**:
1. Ensure participants are speaking clearly
2. Check microphone quality
3. Verify audio levels are adequate
4. Consider implementing Voice Activity Detection (VAD) to skip silent buffers

### 5. Performance Issues

#### ⚠️ "High API usage / Cost"

**Cause**: Batch STT makes 1 API call every 5 seconds per speaker

**Calculations**:
```
2 speakers × 12 calls/minute × 60 minutes = 1,440 calls/hour
At $0.10 per 1000 calls = $0.14/hour
```

**Solutions to reduce cost**:
```python
# 1. Increase buffer duration (fewer calls)
pipeline = AudioPipeline(
    ...,
    buffer_duration_ms=10000  # 10 seconds = half the API calls
)

# 2. Implement Voice Activity Detection
# Skip buffers with no speech (future enhancement)

# 3. Monitor usage in ElevenLabs dashboard
```

#### ⚠️ "Memory usage growing"

**Cause**: Audio buffers not being cleared

**Solutions**:
```python
# 1. Check buffer reset logic (should happen automatically)
# Each buffer is reset after sending to ElevenLabs

# 2. Monitor memory
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Expected: ~0.35 MB for audio buffers (2 speakers × 160KB each)

# 3. Limit session duration
# Restart bot periodically if needed
```

### 6. Dependency Issues

#### ❌ "ModuleNotFoundError: No module named 'aiohttp'"

**Solution**:
```bash
pip install -r requirements.txt

# If that doesn't work
pip install --upgrade pip
pip install aiohttp>=3.9.0
```

#### ❌ "ModuleNotFoundError: No module named 'livekit'"

**Solution**:
```bash
pip install -r requirements.txt

# If that doesn't work
pip install livekit livekit-api
```

#### ❌ "Version conflict"

**Solution**:
```bash
# Create a clean virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 7. Advanced Debugging

#### Enable all logs

```python
import logging

# DEBUG level for everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug.log')
    ]
)

# Very detailed logs for key modules
logging.getLogger("audio_pipeline").setLevel(logging.DEBUG)
logging.getLogger("livekit").setLevel(logging.DEBUG)
logging.getLogger("aiohttp").setLevel(logging.DEBUG)
```

#### Monitor HTTP requests

```bash
# Use Charles Proxy or mitmproxy to inspect HTTP traffic
mitmproxy --mode reverse:https://api.elevenlabs.io --listen-port 8080

# Update code to use proxy (for debugging only)
```

#### Capture audio buffers

```python
# In pipeline.py, add before sending to ElevenLabs:
with open(f"debug_audio_{speaker_label}_{timestamp}.wav", "wb") as f:
    f.write(wav_buffer.getvalue())

# This lets you verify audio format manually
```

### 8. Validation Tests

#### Test 1: LiveKit Connection

```python
from livekit import rtc
import asyncio

async def test_livekit():
    room = rtc.Room()
    await room.connect(LIVEKIT_URL, LIVEKIT_TOKEN)
    print(f"Connected to room: {room.name}")
    print(f"Participants: {len(room.remote_participants)}")
    await room.disconnect()

asyncio.run(test_livekit())
```

#### Test 2: ElevenLabs API

```python
import aiohttp
import asyncio

async def test_elevenlabs():
    headers = {"xi-api-key": ELEVENLABS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.elevenlabs.io/v1/user",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✓ ElevenLabs API OK")
                print(data)
            else:
                print(f"✗ Error: {response.status}")

asyncio.run(test_elevenlabs())
```

#### Test 3: Audio Conversion

```python
from audio_pipeline.audio_converter import AudioConverter
import numpy as np

converter = AudioConverter()

# Create a test signal
audio = np.random.randint(-32768, 32767, 48000, dtype=np.int16)
pcm = converter._resample(audio, 48000, 16000)

print(f"✓ Conversion OK: {len(audio)} → {len(pcm)} samples")
```

## 📞 Support

If the problem persists:

1. **Check the logs** with `LOG_LEVEL=DEBUG`
2. **Review architecture docs**: [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Consult external documentation**:
   - [LiveKit Docs](https://docs.livekit.io/)
   - [ElevenLabs Docs](https://elevenlabs.io/docs)
4. **Create an issue** with:
   - Python version
   - Complete logs
   - Steps to reproduce
   - Configuration (without secrets)

## 🔧 Diagnostic Checklist

Before requesting help, verify:

- [ ] Python >= 3.10
- [ ] All dependencies installed (`pip list`)
- [ ] `.env` file configured correctly
- [ ] LiveKit token valid and not expired
- [ ] ElevenLabs API key valid
- [ ] Participants have joined the room
- [ ] Participants have enabled their microphone
- [ ] DEBUG logs enabled
- [ ] Stable network connection
- [ ] Understanding of batch STT latency (~5-6s per transcript)

## 📝 Bug Report Template

```markdown
**Environment**
- OS: macOS 14.1
- Python: 3.11.5
- Version: 2.0.0

**Configuration**
- LiveKit URL: wss://...
- Room: interview-room
- Language: en
- Buffer duration: 5000ms

**Problem**
Clear description of the problem

**Steps to reproduce**
1. Do X
2. Do Y
3. Error Z

**Logs**
```
[Paste logs here with DEBUG level]
```

**Expected behavior**
What should happen

**Actual behavior**
What actually happens
```

## Known Limitations

### Expected Behavior (Not Bugs)

1. **~5-6 second latency**: This is normal for batch STT
2. **No partial transcripts**: Only final transcripts in batch mode
3. **Transcripts arrive in batches**: Not word-by-word
4. **Potential word cuts at boundaries**: No overlap between 5s windows
5. **Empty transcripts on silence**: Normal if no speech detected in buffer
