# Audio Agents Guide - Real-time Transcription & Evaluation

## 🎙️ What Are Audio Agents?

Audio agents are Python scripts that join LiveKit rooms as participants to:
1. **Transcribe audio** in real-time using ElevenLabs STT
2. **Store transcripts** to JSON and text files
3. **Evaluate interviews** using Claude LLM (optional)

## 📦 Available Scripts

### 1. `run_audio_agent_with_storage.py`
**Purpose:** Real-time transcription with storage only (no LLM evaluation)

**What it does:**
- Joins LiveKit room as "Audio Transcription Agent"
- Transcribes interviewer and candidate audio
- Saves transcripts to `transcripts/` folder:
  - `transcripts.json` - Structured data
  - `transcripts.txt` - Human-readable format

**Use when:** You want transcripts but don't need real-time evaluation

### 2. `run_audio_agent_with_evaluation.py`
**Purpose:** Transcription + real-time LLM evaluation

**What it does:**
- Everything from script #1
- Analyzes conversation every 20 seconds using Claude
- Evaluates:
  - Subject relevance (on/off topic)
  - Question difficulty (easy/medium/hard)
  - Interviewer tone (harsh/neutral/encouraging)
  - Quant Finance topics covered
- Saves evaluations to:
  - `evaluations.json` - Structured evaluations
  - `evaluations.txt` - Human-readable reports

**Use when:** You want real-time interview quality assessment

---

## 🚀 Quick Start

### Prerequisites

1. **Install dependencies:**
```bash
conda activate ttk
pip install -r requirements.txt
```

2. **Configure credentials in `.env`:**
```env
# Required for both scripts
LIVEKIT_URL=wss://your-instance.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
ELEVENLABS_API_KEY=your_elevenlabs_key

# Required for evaluation script only
ANTHROPIC_API_KEY=your_anthropic_key

# Optional: specify room name (default: test1)
LIVEKIT_ROOM=interview-room-001
```

### Running the Scripts

**Option 1: Transcription Only**
```bash
python run_audio_agent_with_storage.py
```

**Option 2: Transcription + Evaluation**
```bash
python run_audio_agent_with_evaluation.py
```

The agent will:
1. Connect to the LiveKit room
2. Wait for participants (interviewer, candidate)
3. Start transcribing audio in real-time
4. Display transcripts in terminal
5. Save everything to `transcripts/` folder

**Stop the agent:** Press `Ctrl+C`

---

## 📊 Understanding the Output

### Terminal Output

**Transcription:**
```
👔 [RECRUITER] ✓ Can you explain what cross-validation is?
👤 [CANDIDATE] ✓ Cross-validation is a technique to assess model performance...
```

- `👔` = Recruiter/Interviewer
- `👤` = Candidate
- `✓` = Final transcript
- `~` = Partial transcript (still being processed)

**Evaluation (if using evaluation script):**
```
────────────────────────────────────────────────────────────────────────────────
🤖 EVALUATION [14:32:15]
────────────────────────────────────────────────────────────────────────────────
📊 Subject: ON_TOPIC (conf: 0.95)
🎯 Difficulty: MEDIUM (conf: 0.85)
💬 Tone: NEUTRAL (conf: 0.90)
📝 Discussing cross-validation techniques and model validation
🔑 Topics: CV_TECHNIQUES, REGULARIZATION
────────────────────────────────────────────────────────────────────────────────
```

### File Output

After running, check `transcripts/` folder:

```
transcripts/
└── interview-room-001_20241115_143205/
    ├── transcripts.json         # Structured transcript data
    ├── transcripts.txt          # Human-readable transcripts
    ├── evaluations.json         # Structured evaluation data (if using evaluation)
    └── evaluations.txt          # Human-readable evaluations (if using evaluation)
```

**transcripts.txt example:**
```
[14:30:12] 👔 RECRUITER: Can you explain what cross-validation is?
[14:30:18] 👤 CANDIDATE: Cross-validation is a technique to assess model performance...
[14:30:45] 👔 RECRUITER: Good. Now explain k-fold cross-validation.
```

**evaluations.txt example:**
```
================================================================================
[14:32:15] EVALUATION
================================================================================
Window: 14:30:00 - 14:30:20
Transcripts: 5

📊 Subject Relevance: ON_TOPIC (confidence: 0.95)
🎯 Question Difficulty: MEDIUM (confidence: 0.85)
💬 Interviewer Tone: NEUTRAL (confidence: 0.90)

📝 Summary: Discussing cross-validation techniques and model validation

🔑 Key Topics: CV_TECHNIQUES, REGULARIZATION
```

---

## 🎯 How Evaluation Works

The evaluation script uses Claude to analyze conversation windows:

### 1. Window-based Analysis
- **Window size:** 20 seconds of conversation
- **Overlap:** 10 seconds between windows (for context)
- **Trigger:** Evaluates every 20s OR when speaker changes

### 2. Quant Finance Topics Tracked

The evaluator recognizes these Hugo's Quant Finance themes:

| Theme | Description |
|-------|-------------|
| `CV_TECHNIQUES` | Cross-validation, K-Fold, Walk-Forward, backtesting |
| `REGULARIZATION` | L1/L2, Lasso, Ridge, overfitting prevention |
| `FEATURE_SELECTION` | Variable selection, SHAP, LIME, PCA |
| `STATIONARITY` | Unit root tests (ADF, KPSS), co-integration |
| `TIME_SERIES_MODELS` | ARIMA, GARCH, VAR, volatility modeling |
| `OPTIMIZATION_PYTHON` | Vectorization, NumPy, Pandas, Numba |
| `LOOKAHEAD_BIAS` | Future data leakage, backtesting errors |
| `DATA_PIPELINE` | Data cleaning, ETL, market data management |
| `BEHAVIORAL_PRESSURE` | Stress handling, deadlines, crisis situations |
| `BEHAVIORAL_TEAMWORK` | Collaboration, conflict management |
| `EXTRA` | Off-topic questions, greetings, transitions |

### 3. Evaluation Criteria

**Subject Relevance:**
- `on_topic` - Discussing technical Quant Finance topics
- `partially_relevant` - Mix of relevant and off-topic
- `off_topic` - Mostly casual chat

**Question Difficulty:**
- `easy` - Basic definitions (e.g., "What is cross-validation?")
- `medium` - Practical applications (e.g., "How would you validate a model?")
- `hard` - Advanced problems (e.g., "Explain look-ahead bias in walk-forward validation")

**Interviewer Tone:**
- `harsh` - Aggressive, dismissive, overly critical
- `neutral` - Professional, balanced, objective
- `encouraging` - Supportive, friendly, positive feedback

### 4. Flags

The evaluator may raise flags like:
- "Harsh tone detected"
- "Off-topic discussion"
- "Look-ahead bias mentioned but not explained"
- "Candidate struggling with basic concepts"

---

## 🔧 Configuration Options

### Change Room Name

**Option 1: Environment variable**
```bash
export LIVEKIT_ROOM=my-interview-room
python run_audio_agent_with_storage.py
```

**Option 2: Edit `.env` file**
```env
LIVEKIT_ROOM=my-interview-room
```

**Option 3: Edit script directly**
```python
LIVEKIT_ROOM = "my-interview-room"  # Change this line
```

### Change Evaluation Window Settings

Edit `run_audio_agent_with_evaluation.py`:

```python
buffer = TranscriptBuffer(
    window_size_seconds=30.0,    # Change from 20 to 30 seconds
    overlap_seconds=15.0,        # Change from 10 to 15 seconds
    min_transcripts_for_evaluation=3  # Require at least 3 transcripts
)
```

### Change Speaker Identities

Edit the pipeline initialization:

```python
pipeline = AudioPipeline(
    ...
    recruiter_identity="john-interviewer",  # Match participant identity
    candidate_identity="jane-candidate"     # Match participant identity
)
```

---

## 🐛 Troubleshooting

### Error: "ELEVENLABS_API_KEY not set"
**Solution:** Add your ElevenLabs API key to `.env`:
```env
ELEVENLABS_API_KEY=sk_your_key_here
```

### Error: "ANTHROPIC_API_KEY not set"
**Solution:** Add your Anthropic API key to `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-your_key_here
```
Get your key from: https://console.anthropic.com/

### Error: "Only 1 participant found, expected 2"
**Cause:** Not enough people in the room

**Solution:**
1. Have interviewer join the room via frontend
2. Have candidate join the room via frontend
3. Then start the audio agent
4. Agent will wait up to 60 seconds for participants

### Error: "Audio track not available"
**Cause:** Participant hasn't enabled microphone

**Solution:**
- Make sure participants have microphones enabled
- Grant browser permission for microphone access
- Check browser console for errors

### Partial transcripts showing but no final transcripts
**Cause:** ElevenLabs STT not committing transcripts

**Solution:**
- Speak louder/clearer
- Check microphone quality
- Verify ElevenLabs API key has credits

### Evaluation not working
**Cause:** Anthropic API issue

**Check:**
1. Is `ANTHROPIC_API_KEY` set correctly?
2. Does your Anthropic account have credits?
3. Check logs for Claude API errors

---

## 💡 Best Practices

### For Transcription
1. **Good audio quality** - Use quality microphones
2. **Clear speech** - Speak clearly, avoid mumbling
3. **One speaker at a time** - Minimize crosstalk
4. **Start agent first** - Launch before participants join

### For Evaluation
1. **Let people talk** - Need at least 2 transcripts per window
2. **Stay on topic** - Evaluator works best with technical discussions
3. **Natural conversation** - Don't force keywords
4. **Review evaluations** - Check JSON files after interview

### For Production
1. **Test first** - Run with test room before real interviews
2. **Monitor logs** - Watch terminal for errors
3. **Check storage** - Verify transcripts are being saved
4. **Backup data** - Copy transcripts folder after each session

---

## 📈 Usage Examples

### Example 1: Quick Test
```bash
# 1. Set room name
export LIVEKIT_ROOM=test-room

# 2. Start transcription agent
python run_audio_agent_with_storage.py

# 3. Join room via frontend (2 people)
# 4. Start talking
# 5. Check transcripts/ folder
```

### Example 2: Full Interview with Evaluation
```bash
# 1. Configure .env with all API keys
nano .env  # Add ANTHROPIC_API_KEY

# 2. Start evaluation agent
python run_audio_agent_with_evaluation.py

# 3. Conduct 30-minute interview
# 4. Stop agent (Ctrl+C)
# 5. Review files:
cat transcripts/interview-room-001_*/evaluations.txt
```

### Example 3: Multiple Sessions
```bash
# Session 1
export LIVEKIT_ROOM=interview-candidate-1
python run_audio_agent_with_evaluation.py
# ... conduct interview ...
# Ctrl+C

# Session 2
export LIVEKIT_ROOM=interview-candidate-2
python run_audio_agent_with_evaluation.py
# ... conduct interview ...
# Ctrl+C

# All sessions saved in separate folders:
# transcripts/interview-candidate-1_timestamp/
# transcripts/interview-candidate-2_timestamp/
```

---

## 🔗 Integration with Frontend

The audio agents work seamlessly with the QuantCoach frontend:

1. **Frontend creates room** via `POST /rooms/create`
2. **Get room name and tokens** from response
3. **Start audio agent** with that room name
4. **Users join** via frontend with their tokens
5. **Agent transcribes** everything automatically

---

## 📊 Analyzing Results

### JSON Format

**transcripts.json:**
```json
{
  "room": "interview-001",
  "session_start": "2024-11-15T14:30:00.000Z",
  "transcripts": [
    {
      "timestamp": "2024-11-15T14:30:12.000Z",
      "speaker": "recruiter",
      "text": "Can you explain cross-validation?",
      "is_final": true
    }
  ]
}
```

**evaluations.json:**
```json
{
  "room": "interview-001",
  "total_evaluations": 5,
  "evaluations": [
    {
      "timestamp": "2024-11-15T14:32:15.000Z",
      "subject_relevance": "on_topic",
      "question_difficulty": "medium",
      "interviewer_tone": "neutral",
      "summary": "Discussing cross-validation techniques",
      "key_topics": ["CV_TECHNIQUES", "REGULARIZATION"],
      "flags": [],
      "confidence_subject": 0.95,
      "confidence_difficulty": 0.85,
      "confidence_tone": 0.90
    }
  ]
}
```

### Python Analysis

```python
import json

# Load transcripts
with open('transcripts/interview-001_timestamp/transcripts.json') as f:
    data = json.load(f)

# Count by speaker
recruiter_count = sum(1 for t in data['transcripts'] if t['speaker'] == 'recruiter')
candidate_count = sum(1 for t in data['transcripts'] if t['speaker'] == 'candidate')

print(f"Recruiter spoke {recruiter_count} times")
print(f"Candidate spoke {candidate_count} times")

# Load evaluations
with open('transcripts/interview-001_timestamp/evaluations.json') as f:
    evals = json.load(f)

# Average difficulty
difficulties = [e['question_difficulty'] for e in evals['evaluations']]
print(f"Question difficulties: {difficulties}")
```

---

## 🚀 Next Steps

1. **Try storage script first** - Get comfortable with basic transcription
2. **Add evaluation** - Test with `ANTHROPIC_API_KEY`
3. **Customize settings** - Adjust window sizes, speaker labels
4. **Build dashboard** - Create UI to view transcripts/evaluations
5. **Add database** - Store results in PostgreSQL/MongoDB
6. **Real-time streaming** - Send transcripts to frontend via WebSocket

---

**Questions?** Check the logs, they're very detailed with emoji indicators! 🎯
