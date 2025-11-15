## 🎯 Project Objective

Create a real-time interview transcription system with automatic speaker identification using **batch-based STT** for simplicity and compatibility.

```
🎤 Interviewer (LiveKit)  ──┐
                            ├──► 🤖 Bot (this project) ──► 📝 Transcripts
🎤 Candidate (LiveKit)   ──┘
                                   (every 5-6 seconds)
```

## 📊 Architecture in 6 Steps

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
    elevenlabs_api_key="...",
    buffer_duration_ms=5000  # 5-second batches
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

**Format:** WebRTC audio frames (often 48kHz, stereo or mono)

### Step 4: Audio Conversion

```
AudioFrame (WebRTC)
    │
    │ 48kHz, Stereo, Int16
    │
    ▼
┌──────────────────┐
│ AudioConverter   │
│                  │
│ • Resample       │ 48kHz → 16kHz
│ • Mix channels   │ Stereo → Mono
│ • Ensure format  │ Int16 → Int16
└────────┬─────────┘
         │
         ▼
PCM bytes (16kHz, mono, 16-bit)
```

**Result:** Audio optimized for STT (32 KB/s)

### Step 5: Audio Buffering

```
Time: 0s ──► 1s ──► 2s ──► 3s ──► 4s ──► 5s
      │                              │
      └────── Accumulate ────────────┘
                  │
                  ▼
           BytesIO Buffer
           160,000 bytes
           (5 seconds)
```

**Key Point:** Unlike streaming, audio is **accumulated locally** before sending.

### Step 6: Batch Transcription

```
Speaker 1 Buffer          Speaker 2 Buffer
  (5 seconds)               (5 seconds)
      │                          │
      ▼                          ▼
ElevenLabs STT            ElevenLabs STT
 (HTTP POST)               (HTTP POST)
      │                          │
      │ ~1 second                │ ~1 second
      │ processing               │ processing
      ▼                          ▼
 Final Transcript          Final Transcript
  (text string)             (text string)
      │                          │
      └────────┬─────────────────┘
               │
               ▼
    Transcript Queue
         (merged)
               │
               ▼
    AsyncIterator[Transcript]
```

**Output:**
```python
Transcript(
    text="Hello, how are you?",
    speaker="recruiter",
    is_final=True  # Always True in batch mode
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
      Audio Stream              Audio Stream
       (WebRTC)                  (WebRTC)
            │                        │
            ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │ LiveKitHandler│        │ LiveKitHandler│
     │  (subscribe)  │        │  (subscribe)  │
     └───────┬───────┘        └───────┬───────┘
             │                        │
       AudioFrames                AudioFrames
             │                        │
             ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │AudioConverter│        │AudioConverter│
     │  (WebRTC →   │        │  (WebRTC →   │
     │   PCM 16kHz) │        │   PCM 16kHz) │
     └───────┬───────┘        └───────┬───────┘
             │                        │
        PCM bytes                 PCM bytes
             │                        │
             ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │  BytesIO     │        │  BytesIO     │
     │  Buffer      │        │  Buffer      │
     │  Accumulate  │        │  Accumulate  │
     │  5 seconds   │        │  5 seconds   │
     └───────┬───────┘        └───────┬───────┘
             │                        │
      When full (160KB)        When full (160KB)
             │                        │
             ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │ Convert to   │        │ Convert to   │
     │ WAV format   │        │ WAV format   │
     └───────┬───────┘        └───────┬───────┘
             │                        │
             ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │  HTTP POST   │        │  HTTP POST   │
     │  ElevenLabs  │        │  ElevenLabs  │
     │  /stt API    │        │  /stt API    │
     └───────┬───────┘        └───────┬───────┘
             │                        │
      text string              text string
             │                        │
             ▼                        ▼
     ┌──────────────┐        ┌──────────────┐
     │ Transcript   │        │ Transcript   │
     │ Object       │        │ Object       │
     │ is_final=True│        │ is_final=True│
     └───────┬───────┘        └───────┬───────┘
             │                        │
             └───────┬────────────────┘
                     │
              asyncio.Queue
               (multiplexer)
                     │
                     ▼
             async for transcript:
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
         ├─ Start buffering recruiter audio
         └─ Start buffering candidate audio

t=3-8s   Buffering phase
         ├─ Accumulate 5 seconds of audio
         └─ Convert frames to PCM continuously

t=8s     First buffer full (recruiter)
         ├─ Convert PCM → WAV
         ├─ Send HTTP POST to ElevenLabs
         └─ Wait for response (~1s)

t=9s     First transcript received
         [recruiter] ✓ "Hello, can you tell me about yourself?"
         ├─ Display to user
         └─ Reset buffer, start next 5s window

t=10s    Second buffer full (candidate)
         ├─ Send to ElevenLabs
         └─ Receive transcript (~1s later)

t=11s    Second transcript
         [candidate] ✓ "Sure, I have 5 years of experience in..."

t=14s    Third transcript (recruiter again)
         [recruiter] ✓ "That's great. What technologies do you use?"

(Continues every 5-6 seconds per speaker)
```

**Key observations:**
- First transcript arrives after ~9 seconds (3s setup + 5s buffer + 1s processing)
- Subsequent transcripts every ~5-6 seconds per speaker
- No partial updates - only final transcripts

## 🎨 Buffering Visualization

### Timeline per Speaker

```
Speaker: Recruiter
─────────────────────────────────────────────────────────►
0s    1s    2s    3s    4s    5s    6s    7s    8s    9s    10s
│                         │                         │
│◄──── Buffer #1 ────────►│                         │
│     Accumulate          │ Send to API             │
│                         │ (~1s processing)        │
│                         │ ▼                       │
│                         │ Transcript #1           │
│                         │                         │
│                         │◄──── Buffer #2 ────────►│
│                         │     Accumulate          │ Send...
│                         │                         │
```

### Buffer States

```
State 1: ACCUMULATING
┌─────────────────────────────┐
│ Buffer: [━━━━━━━━▁▁▁▁▁▁▁▁▁▁] │
│ Progress: 40%               │
│ Size: 64,000 / 160,000      │
└─────────────────────────────┘

State 2: FULL - SENDING
┌─────────────────────────────┐
│ Buffer: [━━━━━━━━━━━━━━━━━━] │
│ Progress: 100%              │
│ Size: 160,000 / 160,000     │
│ Status: Sending to API...   │
└─────────────────────────────┘

State 3: WAITING FOR RESPONSE
┌─────────────────────────────┐
│ HTTP POST in progress...    │
│ Waiting for transcript      │
│ (~500ms - 1000ms)           │
└─────────────────────────────┘

State 4: RECEIVED - RESET
┌─────────────────────────────┐
│ Transcript received!        │
│ Buffer reset to 0           │
│ Starting next window...     │
└─────────────────────────────┘
```

## 📈 Visual Performance

### Latency Breakdown (per transcript)

```
LiveKit frames    ──► [~10ms]   ──► Accumulating...
AudioConverter    ──► [~5ms]    ──►
Buffering phase   ──► [5000ms]  ──► (waiting for full buffer)
WAV conversion    ──► [~5ms]    ──►
HTTP POST         ──► [~20ms]   ──►
ElevenLabs STT    ──► [~1000ms] ──► (cloud processing)
HTTP response     ──► [~20ms]   ──►
Queue processing  ──► [~5ms]    ──►
                  ═══════════════════
Total:            ~6060ms per transcript
```

### Data Flow Rate

```
Audio Capture:
              ↓
PCM chunks:   ~3.2 KB every 100ms
              ↓
Buffer fills: 160 KB every 5 seconds
              ↓
HTTP POST:    1 request every 5 seconds
              ↓
Transcript:   1 text result every ~6 seconds
              ↓
Text output:  ~50-200 bytes every ~6 seconds
```

### Comparison: Batch vs Streaming

```
BATCH STT (Current Implementation)
───────────────────────────────────
Time: 0s ────► 5s ────► 6s
      │        │        │
      Buffer   Send     Result

      [━━━━━━━━━━━━━━━━━] → [📝]

Latency: ~6 seconds
Complexity: Low
API calls: 1 per 5 seconds


STREAMING STT (Not implemented)
────────────────────────────────
Time: 0s ──► 0.5s
      │      │
      Send   Partial
      │      │
      [━━] → [📝~]

      ──► 1s ──► 1.5s
          │      │
          Send   Final
          │      │
          [━━] → [📝✓]

Latency: ~0.5 seconds
Complexity: High (WebSocket)
API calls: Continuous stream
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
         │  BUFFERING   │ ◄──────────┐
         │  (5s windows)│            │
         └──────┬───────┘            │
                │                    │
                ▼                    │
         ┌──────────────┐            │
         │  SENDING     │            │
         │ (HTTP POST)  │            │
         └──────┬───────┘            │
                │                    │
                ▼                    │
         ┌──────────────┐            │
         │  PROCESSING  │            │
         │ (ElevenLabs) │            │
         └──────┬───────┘            │
                │                    │
                ▼                    │
         ┌──────────────┐            │
         │  YIELDING    │            │
         │ (transcript) │────────────┘
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
0:00  [BOT]       Connected to room "interview"
0:02  [BOT]       Found 2 participants
0:03  [BOT]       Buffering started (recruiter, candidate)

0:09  👔 [RECRUITER] ✓ Hello, thank you for joining us today.
0:15  👤 [CANDIDATE] ✓ Thank you for having me, I'm excited to be here.
0:21  👔 [RECRUITER] ✓ Can you tell me about your experience with Python?
0:26  👤 [CANDIDATE] ✓ I have been working with Python for about 5 years.
0:32  👔 [RECRUITER] ✓ That's great! What frameworks do you typically use?
...
```

**Note**: Timestamps show ~6 second gaps between transcripts (normal).

### Example 2: Buffer Windows

```
Speaker: Candidate
Time:    00:00 ─────► 00:05 ─────► 00:06 ─────► 00:11 ─────► 00:12
         │            │            │            │            │
Buffer:  [Accum...    Full]     Reset     [Accum...    Full]     Reset
         │                        │                        │
Output:  │                        └─► "I have been"        └─► "working for"
         │                            "working in"             "five years"
         │                            "software for"
```

**Potential issue**: Words at boundaries (e.g., "for five") might be split across windows.

## 🎓 Key Takeaways

### 1. Batch vs Streaming

```
❌ Streaming (not used)
   Audio → WebSocket → Continuous → Partial → Final
   (complex, low latency)

✓ Batch (current implementation)
   Audio → Buffer (5s) → HTTP POST → Final
   (simple, higher latency)
```

### 2. All transcripts are final

```
Batch: is_final=True
- No partial updates
- Text arrives complete
- Save immediately
- Higher latency but complete sentences

Streaming: is_final=False/True
- Continuous updates
- Partial text first
- Final text later
- Lower latency but more complex
```

### 3. Latency trade-off

```
Buffer size ↔ Latency trade-off

3s buffer:   ~4s total latency, more API calls
5s buffer:   ~6s total latency, balanced  ⭐
10s buffer:  ~11s total latency, fewer API calls
```

### 4. Simple architecture

```
Advantages:
✅ No WebSocket state management
✅ Simple HTTP requests
✅ Easy error handling
✅ No streaming complexity
✅ Works with standard API keys

Trade-offs:
⚠️ Higher latency (~6s vs ~0.5s)
⚠️ No partial transcripts
⚠️ More API calls (vs continuous stream)
⚠️ Potential word cuts at boundaries
```

---

**For technical details:** See [ARCHITECTURE.md](ARCHITECTURE.md)
**For troubleshooting:** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
