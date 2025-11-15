# Audio Pipeline Architecture

## Overview

The Audio Pipeline connects LiveKit (for WebRTC audio) to ElevenLabs STT Realtime (for transcription) with automatic speaker identification.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         LiveKit Room                             │
│  ┌────────────────┐              ┌────────────────┐             │
│  │  Interviewer   │              │   Candidate    │             │
│  │  (Recruiter)   │              │                │             │
│  └───────┬────────┘              └────────┬───────┘             │
│          │                                 │                     │
│      Audio Track                       Audio Track              │
└──────────┼─────────────────────────────────┼───────────────────┘
           │                                 │
           │                                 │
           ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │   LiveKit    │                 │   LiveKit    │
    │   Handler    │                 │   Handler    │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           │ AudioFrames                     │ AudioFrames
           │ (WebRTC)                        │ (WebRTC)
           ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │    Audio     │                 │    Audio     │
    │  Converter   │                 │  Converter   │
    │              │                 │              │
    │ WebRTC → PCM │                 │ WebRTC → PCM │
    │ 16kHz mono   │                 │ 16kHz mono   │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           │ PCM chunks                      │ PCM chunks
           │ (100ms)                         │ (100ms)
           ▼                                 ▼
    ┌──────────────┐                 ┌──────────────┐
    │ ElevenLabs   │                 │ ElevenLabs   │
    │ STT Client   │                 │ STT Client   │
    │ (WebSocket)  │                 │ (WebSocket)  │
    │              │                 │              │
    │ speaker:     │                 │ speaker:     │
    │ "recruiter"  │                 │ "candidate"  │
    └──────┬───────┘                 └──────┬───────┘
           │                                 │
           │ Transcripts                     │ Transcripts
           │ (streaming)                     │ (streaming)
           ▼                                 ▼
    ┌──────────────────────────────────────────┐
    │         Transcript Multiplexer           │
    │                                          │
    │  Merge transcripts from all speakers     │
    │  Maintain speaker labels                 │
    └──────────────┬───────────────────────────┘
                   │
                   │ AsyncIterator[Transcript]
                   ▼
            ┌──────────────┐
            │     User     │
            │  Application │
            └──────────────┘
```

## Main Components

### 1. AudioPipeline (Orchestrator)

**Responsibilities:**
- Initialization of all components
- Data flow orchestration
- Connection lifecycle management
- Multiplexing transcripts from multiple speakers

**Key Methods:**
- `start_transcription() -> AsyncIterator[Transcript]`
- `cleanup()`

### 2. LiveKitHandler

**Responsibilities:**
- Connect to LiveKit room as a bot
- Participant detection and registration
- Audio track management
- Mapping participant → speaker label

**Key Methods:**
- `connect()`
- `get_audio_stream(participant_identity) -> AsyncIterator[AudioFrame]`
- `get_participant_speaker_label(identity) -> str`

### 3. AudioConverter

**Responsibilities:**
- Convert WebRTC frames to PCM
- Resampling (48kHz → 16kHz)
- Multi-channel to mono conversion
- Calculate chunk durations and sizes

**Key Methods:**
- `convert_frame(AudioFrame) -> bytes`
- `calculate_chunk_size(duration_ms) -> int`

### 4. ElevenLabsSTT

**Responsibilities:**
- WebSocket connection to ElevenLabs
- Stream audio to STT API
- Receive real-time transcripts
- Handle partial vs final transcripts

**Key Methods:**
- `connect()`
- `send_audio_chunk(audio_data: bytes)`
- `receive_transcripts() -> AsyncIterator[TranscriptChunk]`

### 5. SpeakerStreamManager

**Responsibilities:**
- Coordination for a specific speaker
- Manage audio → transcription loop
- Buffer audio chunks
- Map TranscriptChunk → Transcript

## Execution Sequence

```
User                AudioPipeline      LiveKitHandler    ElevenLabsSTT    AudioConverter
 │                       │                   │                  │               │
 │ start_transcription() │                   │                  │               │
 ├──────────────────────►│                   │                  │               │
 │                       │                   │                  │               │
 │                       │ connect()         │                  │               │
 │                       ├──────────────────►│                  │               │
 │                       │                   │                  │               │
 │                       │ wait for          │                  │               │
 │                       │ participants      │                  │               │
 │                       │◄──────────────────┤                  │               │
 │                       │                   │                  │               │
 │                       │ create managers   │                  │               │
 │                       │ for each speaker  │                  │               │
 │                       │                   │                  │               │
 │                       │ ┌─────────────────┼──────────────────┼───────────┐   │
 │                       │ │ For each speaker│                  │           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │ connect()       │                  │           │   │
 │                       │ │─────────────────┼─────────────────►│           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │ start_streaming │                  │           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │ get_audio_      │                  │           │   │
 │                       │ │ stream()        │                  │           │   │
 │                       │ │────────────────►│                  │           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │                 │ AudioFrame       │           │   │
 │                       │ │◄────────────────┤                  │           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │ convert_frame() │                  │           │   │
 │                       │ │─────────────────┼──────────────────┼──────────►│   │
 │                       │ │                 │                  │           │   │
 │                       │ │                 │                  │ PCM bytes │   │
 │                       │ │◄────────────────┼──────────────────┼───────────┤   │
 │                       │ │                 │                  │           │   │
 │                       │ │ send_audio_     │                  │           │   │
 │                       │ │ chunk()         │                  │           │   │
 │                       │ │─────────────────┼─────────────────►│           │   │
 │                       │ │                 │                  │           │   │
 │                       │ │                 │    Transcript    │           │   │
 │                       │ │◄────────────────┼──────────────────┤           │   │
 │                       │ │                 │                  │           │   │
 │                       │ └─────────────────┼──────────────────┼───────────┘   │
 │                       │                   │                  │               │
 │                       │ yield Transcript  │                  │               │
 │◄──────────────────────┤                   │                  │               │
 │                       │                   │                  │               │
 │  (loop continues...)  │                   │                  │               │
 │◄──────────────────────┤                   │                  │               │
 │                       │                   │                  │               │
```

## Error Handling

### Circuit Breaker Pattern

To avoid cascading failures, each connection (LiveKit and ElevenLabs) uses a circuit breaker:

```
CLOSED (normal) ──[failures > threshold]──► OPEN (blocking calls)
    ▲                                           │
    │                                           │ [timeout expires]
    │                                           ▼
    │                                      HALF-OPEN (testing)
    └────────────[success]──────────────────────┘
```

### Retry with Exponential Backoff

```python
Initial delay: 1s
├─ Attempt 1: fails → wait 1s
├─ Attempt 2: fails → wait 2s
├─ Attempt 3: fails → wait 4s
└─ Attempt 4: succeeds ✓
```

### Connection Health Monitoring

- Regular ping (every 5s)
- Timeout if no activity > 30s
- Automatic reconnection

## Audio Format

### Input (LiveKit/WebRTC)
- **Format**: Variable (typically 48kHz)
- **Channels**: Mono or stereo
- **Type**: Float32 planar

### Conversion
- **Resampling**: 48kHz → 16kHz (linear interpolation)
- **Mixing**: Stereo → Mono (channel averaging)
- **Type**: Float32 → Int16

### Output (for ElevenLabs)
- **Sample rate**: 16000 Hz
- **Channels**: 1 (mono)
- **Bit depth**: 16-bit
- **Format**: PCM signed integer
- **Chunk size**: 100ms (3200 bytes)

## Performance

### Latency

| Component | Latency | Notes |
|-----------|---------|-------|
| LiveKit → AudioConverter | ~10ms | Local processing |
| AudioConverter | ~5ms | Resampling + conversion |
| WebSocket send | ~20ms | Network dependent |
| ElevenLabs STT | ~200-400ms | Cloud processing |
| **Total** | **~235-435ms** | ✓ < 500ms target |

### Throughput

- **Audio**: ~32 KB/s per speaker (16kHz 16-bit mono)
- **Transcripts**: ~1-5 messages/s per speaker
- **Connections**: 1 LiveKit + N WebSockets (N = number of speakers)

## Security

### Authentication

- **LiveKit**: JWT token with restricted permissions
  - `room_join: true`
  - `can_publish: false` (bot doesn't need to publish)
  - `can_subscribe: true`

- **ElevenLabs**: API key in WebSocket header
  - `xi-api-key: your_key`

### Data

- Audio streamed in real-time, no storage
- Transcripts transmitted immediately
- No persistent cache by default

## Limitations

### Current

1. **Number of speakers**: Maximum 2 (recruiter + candidate)
2. **Language**: Single language per session
3. **Reconnection**: No context recovery after disconnection
4. **Hot-swap**: No handling of participant changes in progress

### Technical

1. **Network latency**: Depends on connection quality
2. **Audio quality**: Requires audio > 8kHz for good transcription
3. **Concurrent speakers**: No overlapping speech handling
4. **Rate limiting**: Subject to ElevenLabs API limits

## Future Enhancements

### Short term
- [ ] Support for more than 2 speakers
- [ ] Automatic language detection
- [ ] Quality metrics (audio level, SNR)

### Medium term
- [ ] Fallback provider (Deepgram, Whisper)
- [ ] Transcript cache and replay
- [ ] Overlapping speech support

### Long term
- [ ] Real-time semantic analysis
- [ ] Emotion detection
- [ ] Automatic summarization
