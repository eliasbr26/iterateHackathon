# Troubleshooting Guide

## 🔍 Common Problems and Solutions

### 1. Connection Errors

#### ❌ "LIVEKIT_TOKEN not set in environment"

**Cause**: Environment variable is not set

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

#### ❌ "Failed to connect to ElevenLabs"

**Possible causes**:
1. Invalid API key
2. Quota exceeded
3. Network issue
4. ElevenLabs service down

**Solutions**:
```bash
# 1. Check the API key
echo $ELEVENLABS_API_KEY

# 2. Test the API key
curl -H "xi-api-key: $ELEVENLABS_API_KEY" \
  https://api.elevenlabs.io/v1/user

# 3. Check the quota
# Go to dashboard.elevenlabs.io

# 4. Check ElevenLabs status
# https://status.elevenlabs.io/
```

### 2. Participant Issues

#### ❌ "Only 0 participant(s) found. Expected at least 2"

**Cause**: Participants have not joined the room before the bot

**Solutions**:
1. **Have participants join BEFORE launching the bot**
2. Increase the wait timeout

```python
# In livekit_handler.py, line ~72
max_wait = 60  # Increase from 30 to 60 seconds
```

#### ❌ "Participant [identity] not found"

**Cause**: Incorrect identity or participant disconnected

**Solutions**:
```python
# Check participant identities in logs
LOG_LEVEL=DEBUG python example_usage.py

# Expected output:
# INFO - Participant connected: interviewer
# INFO - Participant connected: candidate
```

### 3. Audio Issues

#### ❌ "Audio track not available after 30s"

**Possible causes**:
1. Participant has not enabled their microphone
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
```

### 4. Transcription Issues

#### ❌ "No transcripts received"

**Possible causes**:
1. No audio being sent
2. ElevenLabs not detecting speech
3. WebSocket disconnected
4. Incorrect language

**Solutions**:
```python
# 1. Check that audio is being sent
# Logs to look for:
# "Sending audio chunk of X bytes"

# 2. Check the language
pipeline = AudioPipeline(
    ...,
    language="en"  # Or "fr" as needed
)

# 3. Test with known audio content
# Have someone speak clearly

# 4. Check ElevenLabs logs
grep "ElevenLabs" logs.txt
```

#### ❌ "Transcripts are partial only, never final"

**Cause**: ElevenLabs only sends partial transcripts

**Explanation**: This is normal at the beginning of a sentence. Final transcripts arrive when:
- Pause detected (> 500ms)
- End of sentence detected
- Speaker change

**Solution**: Wait a few seconds after speaking

### 5. Performance Issues

#### ⚠️ "High latency (> 1 second)"

**Possible causes**:
1. Slow network connection
2. Audio chunks too large
3. CPU overload
4. Server distance too large

**Solutions**:
```python
# 1. Reduce chunk size
# In pipeline.py, line ~86
target_chunk_size = self.audio_converter.calculate_chunk_size(
    duration_ms=50  # Reduce from 100 to 50ms
)

# 2. Check network latency
ping your-livekit-server.com

# 3. Monitor CPU
top
# or
htop

# 4. Use a geographically closer server
```

#### ⚠️ "Memory usage growing continuously"

**Cause**: Possible memory leak

**Solutions**:
```python
# 1. Check for growing buffers
# In pipeline.py, verify that buffers are properly reset

# 2. Monitor memory
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# 3. Limit session duration
# Restart the bot periodically
```

### 6. Dependency Issues

#### ❌ "ModuleNotFoundError: No module named 'livekit'"

**Solution**:
```bash
pip install -r requirements.txt

# If that doesn't work
pip install --upgrade pip
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
logging.getLogger("websockets").setLevel(logging.DEBUG)
```

#### Use verbose mode

```python
from audio_pipeline.logging_config import setup_colored_logging

setup_colored_logging(level="DEBUG")
```

#### Capture exceptions

```python
import traceback

try:
    async for transcript in pipeline.start_transcription():
        print(transcript)
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
```

#### Monitor WebSockets

```bash
# Use wscat to test ElevenLabs connection
npm install -g wscat

wscat -c "wss://api.elevenlabs.io/v1/convai/conversation/websocket" \
  -H "xi-api-key: your_api_key"
```

### 8. Validation Tests

#### Test 1: LiveKit Connection

```python
from livekit import rtc

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
import requests

headers = {"xi-api-key": ELEVENLABS_API_KEY}
response = requests.get(
    "https://api.elevenlabs.io/v1/user",
    headers=headers
)

if response.status_code == 200:
    print("✓ ElevenLabs API OK")
    print(response.json())
else:
    print(f"✗ Error: {response.status_code}")
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
2. **Search GitHub issues** (if public repo)
3. **Consult the documentation**:
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
- [ ] Unit tests pass (`pytest`)
- [ ] Stable network connection

## 📝 Bug Report Template

```markdown
**Environment**
- OS: macOS 14.1
- Python: 3.11.5
- Version: 1.0.0

**Configuration**
- LiveKit URL: wss://...
- Room: interview-room
- Language: en

**Problem**
Clear description of the problem

**Steps to reproduce**
1. Do X
2. Do Y
3. Error Z

**Logs**
```
[Paste logs here]
```

**Expected behavior**
What should happen

**Actual behavior**
What actually happens
```
