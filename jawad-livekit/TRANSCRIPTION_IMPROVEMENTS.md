# Transcription Quality Improvements

## Issues Identified

After analyzing the audio pipeline and recent transcription sessions, I found several issues causing incomplete transcriptions:

### 1. Voice Activity Detection (VAD) Too Aggressive
**Problem**: ElevenLabs STT was using default VAD settings which may have been too strict, causing it to miss softer speech or speech with pauses.

**Fix**: Added `vad_threshold: 0.3` parameter (lower = more sensitive, catches more speech)
- File: `audio_pipeline/elevenlabs_stt.py:75`

### 2. Audio Chunks Too Small
**Problem**: Sending 100ms audio chunks may not provide enough context for accurate transcription.

**Fix**: Increased chunk size from 100ms to 200ms
- File: `audio_pipeline/pipeline.py:64`
- More audio data per chunk = better transcription accuracy

### 3. Audio Track Timeout Too Short
**Problem**: 30-second timeout was causing "Audio track not available" errors, disrupting the transcription pipeline.

**Evidence from logs**:
```
Error in audio streaming: Audio track not available for agent-simple-507938.852755735 after 30s
```

**Fix**: Increased timeout from 30s to 60s
- File: `audio_pipeline/livekit_handler.py:172`

### 4. Insufficient Stabilization Time
**Problem**: Pipeline started transcribing immediately after detecting 2 participants, but audio tracks may not have been fully established.

**Fix**: Added 5-second stabilization period after finding participants
- File: `audio_pipeline/pipeline.py:192-193`
- Gives audio tracks time to fully connect before starting transcription

## Expected Improvements

With these changes, you should see:
- ✅ More speech captured (fewer missed words/phrases)
- ✅ Fewer connection drops during sessions
- ✅ More stable audio streaming
- ✅ Better handling of speech with natural pauses

## Testing the Improvements

Run the agent again with:
```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
python run_audio_agent_with_storage.py
```

Then conduct a test interview and compare:
- Number of transcripts captured
- Completeness of sentences
- Whether all speech is being transcribed

## Known Limitations (ElevenLabs Free Tier)

The free tier may still have limitations:
- Rate limiting on longer sessions
- Connection timeouts after extended use
- Possible reduced priority for free-tier API keys

If issues persist, consider:
1. Upgrading to paid ElevenLabs tier
2. Switching to alternative STT providers (Deepgram, OpenAI Whisper)
3. Implementing retry logic for dropped connections

## Files Modified

1. `audio_pipeline/elevenlabs_stt.py` - Added VAD threshold parameter
2. `audio_pipeline/pipeline.py` - Increased chunk size and stabilization time
3. `audio_pipeline/livekit_handler.py` - Increased audio track timeout
