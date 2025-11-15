# Real-Time LLM Interview Evaluation System

## Overview

This system adds **real-time AI-powered evaluation** to your interview transcription pipeline using Anthropic Claude.

**Key Features:**
- ✅ Evaluates interviews in **near real-time** (max 30s delay)
- ✅ **No sentence splitting** - uses natural speech boundaries (`is_final` flag)
- ✅ **Context preservation** - 10-second overlap between evaluation windows
- ✅ **Hybrid triggering** - evaluates on time limit OR speaker turn changes
- ✅ Saves both transcripts AND evaluations to files

## Architecture

```
LiveKit Audio → ElevenLabs STT → Transcript Buffer → Claude LLM → Storage
                                      ↓
                              (20s windows with
                               10s overlap)
```

### Components

1. **TranscriptBuffer** (`transcript_buffer.py`)
   - Buffers final transcripts into 20-second windows
   - Triggers evaluation on time limit OR speaker turn
   - Maintains 10-second overlap for context continuity

2. **InterviewEvaluator** (`interview_evaluator.py`)
   - Uses Anthropic Claude for LLM evaluation
   - Analyzes subject relevance, question difficulty, interviewer tone
   - Returns structured JSON with confidence scores

3. **Evaluation Data Models** (`audio_pipeline/models.py`)
   - `BufferedWindow`: Window of transcripts for evaluation
   - `EvaluationResult`: LLM assessment output
   - Enums: `SubjectRelevance`, `QuestionDifficulty`, `InterviewerTone`

## Setup

### 1. Install Dependencies

```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
uv pip install -r requirements.txt
```

### 2. Configure API Keys

Add your Anthropic API key to `../.env`:

```bash
# Existing keys
LIVEKIT_URL=wss://iterate-hackathon-1qxzyt73.livekit.cloud
LIVEKIT_API_KEY=APIgvNeqnUXX3y9
LIVEKIT_API_SECRET=XqU85wFfZwxVHUZU7hgkzbBOfaGNL4l1xChephaYL9XB
ELEVENLABS_API_KEY=sk_6b30b9a41e477733c0e8e9726645c38aafbb7deef8dd0beb

# Add this line:
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

Get your Anthropic API key from: https://console.anthropic.com/

## Usage

### Run with Real-Time Evaluation

```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
python run_audio_agent_with_evaluation.py
```

### What You'll See

#### Console Output

```
================================================================================
🎙️  REAL-TIME AUDIO TRANSCRIPTION + LLM EVALUATION
================================================================================

👔 [RECRUITER] ✓ Tell me about your experience with Python
👤 [CANDIDATE] ✓ I've been working with Python for 3 years...

────────────────────────────────────────────────────────────────────────────────
🤖 EVALUATION [18:30:45]
────────────────────────────────────────────────────────────────────────────────
📊 Subject: ON_TOPIC (conf: 0.95)
🎯 Difficulty: MEDIUM (conf: 0.85)
💬 Tone: NEUTRAL (conf: 0.90)
📝 Interviewer asking about Python experience, candidate providing relevant background
🔑 Topics: Python programming, work experience
────────────────────────────────────────────────────────────────────────────────
```

#### Saved Files

All data is saved to `transcripts/{room}_{timestamp}/`:

1. **transcripts.json** - All transcripts in JSON format
2. **transcripts.txt** - Human-readable transcript log
3. **evaluations.json** - All LLM evaluations in JSON format
4. **evaluations.txt** - Human-readable evaluation report

Example evaluation output:

```
================================================================================
[18:30:45] EVALUATION
================================================================================
Window: 18:30:25 - 18:30:45
Transcripts: 5

📊 Subject Relevance: ON_TOPIC (confidence: 0.95)
🎯 Question Difficulty: MEDIUM (confidence: 0.85)
💬 Interviewer Tone: NEUTRAL (confidence: 0.90)

📝 Summary: Interviewer asking about Python experience, candidate providing relevant background

🔑 Key Topics: Python programming, work experience

```

## Evaluation Criteria

### Subject Relevance
- **on_topic**: Professional topics, skills, experience relevant to job
- **partially_relevant**: Mix of relevant and casual/off-topic content
- **off_topic**: Mostly unrelated to interview purpose
- **unknown**: Insufficient data to assess

### Question Difficulty
- **easy**: Basic background questions, simple definitions
- **medium**: Moderate technical questions, behavioral questions
- **hard**: Advanced technical problems, complex scenarios
- **unknown**: No clear questions asked yet

### Interviewer Tone
- **harsh**: Aggressive, dismissive, overly critical
- **neutral**: Professional, balanced, objective
- **encouraging**: Supportive, friendly, helpful
- **unknown**: Insufficient data to assess

## Configuration Options

You can customize the behavior by modifying `run_audio_agent_with_evaluation.py`:

```python
# Adjust buffer settings
buffer = TranscriptBuffer(
    window_size_seconds=20.0,      # Evaluation window size
    overlap_seconds=10.0,           # Context overlap between windows
    min_transcripts_for_evaluation=2  # Minimum transcripts needed
)

# Change Claude model
evaluator = InterviewEvaluator(
    api_key=ANTHROPIC_API_KEY,
    model="claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229"
)
```

### Tuning Parameters

**Window Size (20s default)**
- **Smaller (15s)**: Faster feedback, less context
- **Larger (30s)**: Better context, slower feedback (max allowed)

**Overlap (10s default)**
- **More overlap**: Better context continuity, more redundant processing
- **Less overlap**: Lower API costs, may lose some context

**Minimum Transcripts (2 default)**
- Increase if evaluations triggering too early with incomplete data

## Trigger Logic

The system uses **hybrid triggering**:

1. **Time-based**: Evaluates when window reaches 20 seconds
2. **Speaker turn**: Evaluates when speaker changes (if >5s of content)

This ensures:
- Natural evaluation boundaries (complete questions/answers)
- Max 30-second delay from speech to evaluation
- No mid-sentence cuts

## API Costs

### Anthropic Claude Pricing (as of 2025)

**Claude 3.5 Sonnet** (recommended):
- Input: $3 per million tokens
- Output: $15 per million tokens

**Estimated costs per interview:**
- 30-minute interview ≈ 6,000 words ≈ 8,000 tokens
- With 20s windows + 10s overlap ≈ 120 evaluations
- **Total cost: ~$0.50 - $1.00 per 30-min interview**

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
→ Add `ANTHROPIC_API_KEY=your-key` to `../.env` file

### Evaluations not appearing
→ Check that you have at least 2 final transcripts before 20s window
→ Verify transcripts are marked `is_final=True`

### "Invalid JSON response from Claude"
→ Claude occasionally adds markdown formatting
→ The parser handles this automatically
→ Check `raw_llm_response` in `evaluations.json` for debugging

### Slow evaluations
→ Claude API latency is typically 1-3 seconds
→ Evaluations run in background worker (non-blocking)
→ Multiple evaluations can queue up during fast conversations

## Development

### Running Tests

```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
pytest tests/
```

### Debug Logging

Enable debug mode for more detailed logs:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

Potential enhancements:
- [ ] Add evaluation history to LLM context (evaluate trends)
- [ ] Support for multiple languages
- [ ] Real-time alerts for specific flags (harsh tone, off-topic)
- [ ] Dashboard visualization of evaluation metrics
- [ ] Integration with candidate scoring system

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     LiveKit Interview Room                      │
│  👔 Recruiter Audio ──────┐    👤 Candidate Audio ──────┐      │
└──────────────────────────┼──────────────────────────────┼───────┘
                           │                              │
                           ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audio Pipeline Agent                         │
│  ┌──────────────┐      ┌──────────────┐                        │
│  │ ElevenLabs   │ ───▶ │  Transcript  │                        │
│  │     STT      │      │   Storage    │                        │
│  └──────────────┘      └──────────────┘                        │
│         │                                                        │
│         │ (is_final=True transcripts)                           │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  Transcript  │ ◀── 20s window                               │
│  │    Buffer    │ ◀── 10s overlap                              │
│  │              │ ◀── Speaker turn detection                   │
│  └──────────────┘                                               │
│         │                                                        │
│         │ (BufferedWindow)                                      │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  Interview   │ ───▶ Anthropic Claude API                    │
│  │  Evaluator   │      (claude-3-5-sonnet)                     │
│  └──────────────┘                                               │
│         │                                                        │
│         │ (EvaluationResult)                                    │
│         ▼                                                        │
│  ┌──────────────┐                                               │
│  │  Evaluation  │                                               │
│  │   Storage    │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
         📁 transcripts/{room}_{timestamp}/
            ├── transcripts.json
            ├── transcripts.txt
            ├── evaluations.json
            └── evaluations.txt
```

## Files Modified/Created

### New Files
- `transcript_buffer.py` - Windowed buffering system
- `interview_evaluator.py` - Claude LLM integration
- `run_audio_agent_with_evaluation.py` - Integrated runner
- `LLM_EVALUATION_README.md` - This documentation

### Modified Files
- `audio_pipeline/models.py` - Added evaluation data models
- `requirements.txt` - Added anthropic package

### No Changes Required
- `run_audio_agent_with_storage.py` - Still works without evaluation
- `audio_pipeline/pipeline.py` - No changes to core pipeline
- `client-for-friends.html` - Client interface unchanged
