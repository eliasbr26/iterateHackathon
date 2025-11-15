# Visual Guide - Audio Pipeline

## 🎯 Project Objective

Create a real-time transcription system for interviews with automatic speaker identification.

```
🎤 Interviewer (LiveKit)  ──┐
                            ├──► 🤖 Bot (this project) ──► 📝 Transcripts
🎤 Candidate (LiveKit)   ──┘
```

## 📊 Architecture in 5 Steps

### Step 1: LiveKit Connection
```
     ┌─────────────────┐
     │  LiveKit Room   │
     │  "interview"    │
     └────────┬────────┘
              │
         ┌────▼────┐
         │   Bot   │ ← AudioPipeline.start_transcription()
         └─────────┘
```

**Code:**
```python
pipeline = AudioPipeline(
    livekit_url="wss://...",
    livekit_room="interview",
    livekit_token="...",
    elevenlabs_api_key="..."
)
```

### Step 2: Participant Detection
```
LiveKit Room
    │
    ├─► 👔 Participant 1 (identity="interviewer")
    │   → Speaker label: "recruiter"
    │
    └─► 👤 Participant 2 (identity="candidate")
        → Speaker label: "candidate"
```

**Automatic mapping:**
- Identity contains "interviewer" → speaker = "recruiter"
- Identity contains "candidate" → speaker = "candidate"

### Step 3: Audio Capture
```
Participant 1           Participant 2
     🎤                      🎤
     │                       │
Audio Track            Audio Track
  (WebRTC)              (WebRTC)
     │                       │
     ├──────────┬────────────┤
                │
         LiveKitHandler
         get_audio_stream()
```

**Format:** WebRTC audio frames (often 48kHz, stereo)

### Step 4: Audio Conversion
```
AudioFrame (WebRTC)
    │
    │ 48kHz, Stereo, Float32
    │
    ▼
┌──────────────────┐
│ AudioConverter   │
│                  │
│ • Resample       │ 48kHz → 16kHz
│ • Mix channels   │ Stereo → Mono
│ • Convert format │ Float32 → Int16
└────────┬─────────┘
         │
         ▼
PCM bytes (16kHz, mono, 16-bit)
```

**Result:** Audio optimized for STT (32 KB/s)

### Step 5: Real-time Transcription
```
Speaker 1 PCM          Speaker 2 PCM
     │                      │
     ▼                      ▼
ElevenLabs STT        ElevenLabs STT
(WebSocket #1)        (WebSocket #2)
     │                      │
     │ Transcripts          │ Transcripts
     │ speaker="recruiter"  │ speaker="candidate"
     │                      │
     └──────────┬───────────┘
                │
                ▼
    AsyncIterator[Transcript]
         (merged stream)
```

**Output:**
```python
Transcript(
    text="Hello, how are you?",
    speaker="recruiter",
    is_final=True
)
```

## 🔄 Detailed Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      LIVEKIT ROOM                           │
│                                                             │
│  👔 Interviewer              👤 Candidate                   │
│  (microphone active)         (microphone active)           │
└───────────┬────────────────────────┬────────────────────────┘
            │                        │
            │ Audio Track 1          │ Audio Track 2
            │ (WebRTC)               │ (WebRTC)
            ▼                        ▼
    ┌───────────────┐        ┌───────────────┐
    │ AudioFrame    │        │ AudioFrame    │
    │ 48kHz/stereo  │        │ 48kHz/stereo  │
    └───────┬───────┘        └───────┬───────┘
            │                        │
            ▼                        ▼
    ┌───────────────┐        ┌───────────────┐
    │ AudioConverter│        │ AudioConverter│
    │ ↓ 16kHz/mono  │        │ ↓ 16kHz/mono  │
    └───────┬───────┘        └───────┬───────┘
            │                        │
            │ PCM chunks (100ms)     │ PCM chunks (100ms)
            ▼                        ▼
    ┌───────────────┐        ┌───────────────┐
    │ ElevenLabs    │        │ ElevenLabs    │
    │ WebSocket #1  │        │ WebSocket #2  │
    │               │        │               │
    │ speaker:      │        │ speaker:      │
    │ "recruiter"   │        │ "candidate"   │
    └───────┬───────┘        └───────┬───────┘
            │                        │
            │ Transcripts            │ Transcripts
            │ (partial + final)      │ (partial + final)
            └────────┬───────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   Multiplexer   │
            │  (merge queue)  │
            └────────┬────────┘
                     │
                     ▼
         async for transcript in ...:
            print(transcript)
```

## ⏱️ Execution Timeline

```
t=0s     Bot starts
         ├─ Connect to LiveKit
         └─ Wait for participants

t=2s     Participants join
         ├─ Interviewer detected → "recruiter"
         └─ Candidate detected → "candidate"

t=3s     Audio tracks available
         ├─ Connect ElevenLabs #1 (recruiter)
         └─ Connect ElevenLabs #2 (candidate)

t=3.1s   Streaming begins
         ├─ Audio frames → conversion → ElevenLabs
         └─ Latency: ~100ms per chunk

t=4s     Interviewer starts speaking
         "Hello, can you tell me..."
         ↓
t=4.2s   First partial transcript
         [recruiter] ~ "Hello"

t=4.5s   Partial transcript updated
         [recruiter] ~ "Hello, can you tell"

t=5s     End of sentence detected
         [recruiter] ✓ "Hello, can you tell me about yourself?"
         (is_final=True)

t=6s     Candidate responds
         "Sure, I have 5 years..."
         ↓
t=6.3s   [candidate] ~ "Sure"
t=7s     [candidate] ✓ "Sure, I have 5 years of experience."
```

## 🎨 Transcript Lifecycle

```
                   User speaks
                       │
                       ▼
         ┌─────────────────────────┐
         │  Audio buffering        │
         │  (100ms chunks)         │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  Send to ElevenLabs     │
         │  (WebSocket)            │
         └──────────┬──────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  STT processing         │
         │  (200-400ms)            │
         └──────────┬──────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
┌────────────────┐    ┌────────────────┐
│ Partial result │    │ Final result   │
│ is_final=False │    │ is_final=True  │
│ (continues)    │    │ (complete)     │
└────────────────┘    └────────────────┘
        │                        │
        ▼                        ▼
 Show updating          Save to storage
 (overwrite display)    (persistent)
```

## 📈 Visual Performance

### Latency per component
```
LiveKit frame     ──► [~10ms]  ──►
AudioConverter    ──► [~5ms]   ──►
Network send      ──► [~20ms]  ──►
ElevenLabs STT    ──► [~200ms] ──►
Network recv      ──► [~20ms]  ──►
Processing        ──► [~10ms]  ──►
                  ═══════════════
Total             ──► ~265ms   ✓
```

### Throughput
```
Audio input:  32 KB/s per speaker
              ↓
WebSocket:    10 chunks/s (100ms chunks)
              ↓
Transcripts:  1-5 messages/s per speaker
              ↓
Text output:  ~100-500 bytes/s
```

## 🔍 System States

```
         ┌──────────────┐
         │  STARTING    │
         │  (init)      │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ CONNECTING   │
         │ (LiveKit)    │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │  WAITING     │
         │ (participants)│
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │  READY       │
         │ (streaming)  │◄───┐
         └──────┬───────┘    │
                │             │
     ┌──────────┼─────────┐   │
     │          │         │   │
     ▼          ▼         ▼   │
┌─────────┐ ┌─────┐  ┌──────┐│
│RECEIVING│ │ERROR│  │RETRY ├┘
│(transcr.)│ │     │  │      │
└─────────┘ └──┬──┘  └──────┘
                │
                ▼
         ┌──────────────┐
         │  STOPPING    │
         │  (cleanup)   │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │   STOPPED    │
         └──────────────┘
```

## 💡 Visual Examples

### Example 1: Normal Interview
```
Timeline:
0:00 [BOT]       Connected to room "interview"
0:02 [BOT]       Found 2 participants
0:03 [BOT]       Streaming started

0:05 👔 [RECRUITER] ✓ Hello, thank you for joining us today.
0:08 👤 [CANDIDATE] ✓ Thank you for having me.
0:10 👔 [RECRUITER] ✓ Can you tell me about your experience?
0:12 👤 [CANDIDATE] ~ I have been working in...
0:14 👤 [CANDIDATE] ✓ I have been working in software for 5 years.
0:18 👔 [RECRUITER] ✓ That's great! What technologies do you use?
...
```

### Example 2: Partial Transcripts
```
Time    Display
────    ───────────────────────────────────────
0:00    [CANDIDATE] ~ "I"
0:01    [CANDIDATE] ~ "I have"
0:02    [CANDIDATE] ~ "I have been"
0:03    [CANDIDATE] ~ "I have been working"
0:04    [CANDIDATE] ✓ "I have been working in Python."
        └── Final transcript saved
```

## 🎓 Key Takeaways

### 1. One WebSocket per speaker
```
❌ Wrong (diarization on ElevenLabs side)
   All audio → 1 WebSocket → Diarization
   (less accurate, increased latency)

✓ Good (separation on LiveKit side)
   Speaker 1 → WebSocket 1 → Transcripts
   Speaker 2 → WebSocket 2 → Transcripts
   (more accurate, parallel)
```

### 2. Partial vs final transcripts
```
Partial: is_final=False
- Continuous updates
- Can change
- Real-time display
- Don't save

Final: is_final=True
- Complete and stable
- Won't change
- Save it
- Use for analysis
```

### 3. Optimal latency
```
Chunk size ↔ Latency trade-off

50ms chunks:  Low latency, more requests
100ms chunks: ⭐ Sweet spot (recommended)
200ms chunks: Higher latency, fewer requests
```

---

**For more details:** See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
