# Implementation Guide: Automated Backend + Live Visualizations

## Overview

This implementation adds:
1. **Automated backend** - No more manual `export LIVEKIT_ROOM` and agent startup
2. **Live transcript streaming** - Real-time transcripts via Server-Sent Events (SSE)
3. **Beautiful visualizations** - 6 new visualization components with real-time updates

---

## What Was Implemented

### Backend Changes (`quantcoach-livekit/backend/`)

#### 1. **Agent Lifecycle Management**
- **File**: `agent_manager.py` (new)
- **Purpose**: Manages agent processes for different rooms
- **Features**:
  - Start/stop agents programmatically
  - Track agent status (running/stopped/error)
  - Handle errors gracefully

#### 2. **Refactored Agent Script**
- **File**: `run_audio_agent_with_evaluation.py` (modified)
- **Changes**:
  - Converted `main()` to `run_agent()` function accepting parameters
  - Added `event_callback` parameter for real-time event publishing
  - Backward compatible with CLI usage (can still run manually)

#### 3. **Enhanced Server with SSE & Auto-start**
- **File**: `server.py` (modified)
- **New Features**:
  - **Auto-start agent**: When you create a room, the agent starts automatically
  - **SSE streaming**: `GET /rooms/{room_name}/stream` - Real-time transcript/evaluation stream
  - **Analytics endpoint**: `GET /rooms/{room_name}/analytics` - Aggregated metrics
  - **Agent status**: `GET /rooms/{room_name}/status` - Check if agent is running

#### 4. **Dependencies**
- **Added**: `sse-starlette>=2.1.0` to `requirements.txt`

---

### Frontend Changes (`quantcoach-livekit/frontend/`)

#### 1. **Real-time Data Hook**
- **File**: `src/hooks/useTranscriptStream.ts` (new)
- **Purpose**: Connects to backend SSE stream
- **Features**:
  - Auto-reconnection on disconnect
  - Parses transcript and evaluation events
  - Stores data in React state

#### 2. **Updated API Service**
- **File**: `src/services/api.ts` (modified)
- **New Methods**:
  - `getAnalytics(roomName)` - Fetch aggregated analytics
  - `getAgentStatus(roomName)` - Check agent status

#### 3. **New Visualization Components**

| Component | Purpose | Visualization Style |
|-----------|---------|-------------------|
| **DifficultyBar** | Shows interview difficulty (cold/hot) | Horizontal slider with blue→yellow→red gradient |
| **TopicCoverageRadar** | Shows which of 11 topics discussed | Radar chart with topic labels |
| **RedFlagPanel** | Alerts for off-topic, low confidence | Scrollable alert cards with severity badges |
| **ToneIndicator** | Interviewer tone (harsh/neutral/encouraging) | Card with emoji, color, and scale |
| **InterviewTimeline** | Timeline of interview segments | Horizontal timeline with color-coded blocks |
| **ConfidenceMeters** | AI confidence in assessments | Progress bars for 3 metrics |

#### 4. **Updated Dashboard**
- **File**: `src/pages/Index.tsx` (complete rewrite)
- **New Layout**:
  ```
  [Video Area]
  ┌─────────────┬──────────────────┬─────────────┐
  │ Tone        │ Difficulty Bar   │ Red Flags   │
  │ Confidence  │                  │             │
  │ Metrics     │ Transcript Feed  │             │
  │             │                  │             │
  ├─────────────┴──────────────────┴─────────────┤
  │ Topic Radar │ Interview Timeline             │
  └─────────────┴────────────────────────────────┘
  [Coverage Progress Bar]
  ```

---

## How to Use

### 1. Start the Backend

```bash
cd quantcoach-livekit/backend

# Make sure dependencies are installed
pip install -r requirements.txt

# Start the FastAPI server
python server.py
```

The server will start on `http://0.0.0.0:8000`

### 2. Start the Frontend

```bash
cd quantcoach-livekit/frontend

# Install dependencies (if needed)
npm install

# Start the dev server
npm run dev
```

The frontend will start on `http://localhost:5173` (or similar)

### 3. Create a Room & Start Interview

**Option A: Using the Frontend**
1. Open the frontend in your browser
2. Click "Create Room" in the VideoArea component
3. **Agent auto-starts!** No manual setup needed
4. Join the room as interviewer/candidate
5. Start speaking - transcripts appear in real-time!

**Option B: Using the API**
```bash
# Create a room (agent auto-starts)
curl -X POST http://localhost:8000/rooms/create \
  -H "Content-Type: application/json" \
  -d '{"room_name": "my-interview"}'

# Check agent status
curl http://localhost:8000/rooms/my-interview/status

# Stream live data (in browser or with EventSource)
# Open: http://localhost:8000/rooms/my-interview/stream
```

### 4. View Visualizations

- **Demo Mode**: Toggle "Demo Mode" in the dashboard header to see visualizations with sample data
- **Live Mode**: Disable demo mode to see real-time data from the agent

---

## Visualization Features

### 🧊🔥 Difficulty Bar (Cold-Hot Score)
- **Blue** = Easy questions (cold)
- **Yellow** = Medium difficulty (warm)
- **Red** = Hard questions (hot)
- Weighted average of recent evaluations

### 🚩 Red Flags
Automatically detects:
- **Off-topic discussions** (critical)
- **Partially relevant topics** (warning)
- **Low AI confidence** < 70% (warning)
- **LLM-generated suggestions** (info)

### 📊 Topic Coverage Radar
Shows coverage of all 11 topics:
- CV_TECHNIQUES
- REGULARIZATION
- FEATURE_SELECTION
- STATIONARITY
- TIME_SERIES_MODELS
- OPTIMIZATION_PYTHON
- LOOKAHEAD_BIAS
- DATA_PIPELINE
- BEHAVIORAL_PRESSURE
- BEHAVIORAL_TEAMWORK
- EXTRA

### 😊 Tone Indicator
- 😠 **Harsh** (red) - Direct, challenging tone
- 😐 **Neutral** (gray) - Balanced, professional
- 😊 **Encouraging** (green) - Supportive, positive

### 📈 Interview Timeline
Color-coded segments showing:
- **Border color** = Difficulty (blue/yellow/red)
- **Fill color** = Relevance (green=on-topic, red=off-topic, yellow=partial)
- **Hover** = See summary, topics, confidence

### 🎯 Confidence Meters
Shows AI confidence in:
- Subject relevance assessment
- Question difficulty classification
- Tone evaluation

---

## API Endpoints

### Room Management
- `POST /rooms/create` - Create room + auto-start agent
- `GET /rooms` - List all rooms
- `GET /rooms/{room_name}/participants` - List participants
- `DELETE /rooms/{room_name}` - Delete room + stop agent

### Real-time Data
- `GET /rooms/{room_name}/stream` - SSE stream (transcripts + evaluations)
- `GET /rooms/{room_name}/analytics` - Aggregated metrics
- `GET /rooms/{room_name}/status` - Agent status

---

## Data Flow

```
┌─────────────┐
│  User joins │
│    room     │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  POST /rooms/   │  Auto-starts agent
│     create      │  ───────────────────►  AgentManager
└────────┬────────┘                            │
         │                                     │
         │                                     ▼
         │                            ┌────────────────┐
         │                            │  AudioPipeline │
         │                            │  + Evaluator   │
         │                            └────────┬───────┘
         │                                     │
         │                                     │ Events
         │                                     ▼
         │                            ┌────────────────┐
         │                            │  Event Queue   │
         │                            │   (in-memory)  │
         │                            └────────┬───────┘
         │                                     │
         │                                     │ SSE Stream
         ▼                                     ▼
┌──────────────────┐                  ┌────────────────┐
│  Frontend opens  │◄─────────────────│  GET /stream   │
│   SSE connection │                  └────────────────┘
└────────┬─────────┘
         │
         │ Real-time updates
         ▼
┌──────────────────┐
│  Visualizations  │
│    update live   │
└──────────────────┘
```

---

## Troubleshooting

### Backend Issues

**Problem**: Agent doesn't start automatically
- **Check**: AgentManager initialization logs in server.py
- **Solution**: Ensure `ELEVENLABS_API_KEY` and `ANTHROPIC_API_KEY` are set in `.env`

**Problem**: SSE stream not connecting
- **Check**: Browser console for connection errors
- **Solution**: Verify CORS settings in server.py, check that port 8000 is accessible

**Problem**: "No module named 'sse_starlette'"
- **Solution**: `pip install sse-starlette>=2.1.0`

### Frontend Issues

**Problem**: Components not rendering
- **Check**: Browser console for import errors
- **Solution**: Ensure all dependencies installed: `npm install`

**Problem**: No real-time data appearing
- **Check**: Demo mode is OFF
- **Check**: SSE connection indicator shows "Live data streaming"
- **Solution**: Verify backend is running and agent is started

**Problem**: TypeScript errors
- **Solution**: Check that all new files are in correct directories
- **Solution**: Restart TypeScript server in VS Code

---

## Testing

### Test the Complete Flow

1. **Start backend**: `cd backend && python server.py`
2. **Start frontend**: `cd frontend && npm run dev`
3. **Create room**: Click "Create Room" in UI
4. **Join room**: Use the generated tokens to join
5. **Speak**: Say something related to quantitative finance
6. **Verify**:
   - Transcripts appear in center panel
   - Difficulty bar shows position
   - Tone indicator updates
   - Topic radar shows covered topics
   - Timeline adds new segments
   - Red flags appear if off-topic

### Test Demo Mode

1. Toggle "Demo Mode" ON in dashboard header
2. Verify all visualizations work with sample data
3. Toggle OFF to see live data

---

## Configuration

### Backend Environment Variables

Create/update `quantcoach-livekit/backend/.env`:

```bash
# Required
LIVEKIT_URL=wss://your-livekit-server.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
ELEVENLABS_API_KEY=your-elevenlabs-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### Frontend Environment Variables

Create `quantcoach-livekit/frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
```

---

## What's Next?

Potential enhancements:
1. **Persistent storage**: Save sessions to database instead of in-memory
2. **Room name input**: Allow users to specify room name in UI
3. **Historical analysis**: View past interview sessions
4. **Export reports**: Download PDF/CSV of analytics
5. **Multi-room support**: Monitor multiple interviews simultaneously
6. **WebSocket option**: Alternative to SSE for bi-directional communication

---

## Summary

### Before
```bash
# Manual process:
export LIVEKIT_ROOM=test1
python run_audio_agent_with_evaluation.py
# Wait for completion
# Open transcripts/test1_timestamp/transcripts.txt
```

### After
```bash
# Automated:
python server.py  # Backend with auto-start
npm run dev      # Frontend with live visualizations
# Create room → Agent auto-starts → Live data streams → Beautiful visualizations!
```

✅ **No more manual room setup**
✅ **Live transcript streaming**
✅ **Beautiful real-time visualizations**
✅ **Cold-hot difficulty score**
✅ **Red flags for off-topic discussions**
✅ **Topic coverage radar**
✅ **Interview timeline**
✅ **Tone indicators**
✅ **Confidence meters**

---

**Implementation Date**: 2025
**Technologies**: FastAPI, SSE, React, TypeScript, Recharts, Shadcn/UI
