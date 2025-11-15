# Quick Start Guide

## Your LiveKit Setup

✅ **LiveKit Cloud is configured!**
- URL: `wss://iterate-hackathon-1qxzyt73.livekit.cloud`
- API credentials are set in `.env`

## Important: The LiveKit Server is Already Running

**You DO NOT need to run a LiveKit server yourself!**

LiveKit Cloud (`iterate-hackathon-1qxzyt73.livekit.cloud`) is already running in the cloud and ready to accept connections. Your application just needs to connect to it.

## What Runs Where?

```
┌─────────────────────────────────────┐
│   LiveKit Cloud (Already Running)   │  ← In the cloud, you don't start this
│   iterate-hackathon-1qxzyt73        │
│   Handles video/audio streaming     │
└─────────────────────────────────────┘
              ▲
              │ Connects to
              │
┌─────────────────────────────────────┐
│   Your Local Application            │  ← You run these:
│                                     │
│   1. FastAPI Server (server.py)    │  ← Run this first
│   2. Agent (interview_agent.py)    │  ← Run this second (optional)
│   3. Client (client.html)          │  ← Open in browser
└─────────────────────────────────────┘
```

## Step-by-Step: Running Your Application

### Terminal 1: Start the API Server

```bash
cd jawad-livekit
./run.sh
```

Or manually:
```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
python server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!**

### Terminal 2: Start the Agent (Optional but recommended)

```bash
cd jawad-livekit
source ../iterate-hack/bin/activate
python interview_agent.py dev
```

**Note:** You need OpenAI and Deepgram API keys for the agent to work. If you don't have them yet, skip this step - the video rooms will still work without the agent.

### Open the Client

```bash
# From the jawad-livekit directory
open client.html

# Or on Linux:
xdg-open client.html

# Or just double-click client.html in your file browser
```

## Testing the Setup

### Test 1: Check API is Running

Open: http://localhost:8000

You should see:
```json
{
  "status": "ok",
  "service": "LiveKit Interview API",
  "version": "1.0.0"
}
```

### Test 2: Create a Room

1. Open `client.html` in your browser
2. Leave room name blank
3. Select "Interviewer"
4. Enter your name
5. Click "Create/Join Room"

If everything works, you'll:
- See yourself in the video
- Get a room name like `interview-20241115-143000`
- Be connected to LiveKit Cloud!

### Test 3: Join from Another Window

1. Open `client.html` in a new browser window (or incognito)
2. Enter the room name from Test 2
3. Select "Candidate"
4. Enter a different name
5. Click "Create/Join Room"

You should now see both participants in both windows!

## Troubleshooting

### "Failed to create room"
- Check that `.env` has the correct LiveKit credentials
- Make sure `server.py` is running

### Video not working
- Allow camera/microphone permissions in your browser
- Try Chrome or Firefox (Safari can be problematic)

### Agent not starting
The agent needs these API keys in `.env`:
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `DEEPGRAM_API_KEY` - Get from https://console.deepgram.com/

If you don't have these, you can still use video rooms - just skip the agent!

## What Each Component Does

| Component | Purpose | Required? |
|-----------|---------|-----------|
| **LiveKit Cloud** | Video/audio streaming server | ✅ Yes (already running) |
| **server.py** | Creates rooms, generates tokens | ✅ Yes |
| **interview_agent.py** | Transcribes conversations | ⚠️ Optional |
| **client.html** | Web interface for participants | ✅ Yes |

## Next Steps

Once you have it working:

1. **Add API Keys** (if not done):
   - OpenAI: https://platform.openai.com/api-keys
   - Deepgram: https://console.deepgram.com/

2. **Test the Agent**:
   - Start the agent in Terminal 2
   - Join a room and talk
   - Watch the agent terminal for transcripts

3. **Customize**:
   - Modify `interview_agent.py` to add analysis
   - Update `client.html` for better UI
   - Add sentiment analysis or other features

## Quick Reference

### Start Everything
```bash
# Terminal 1 - API Server
cd jawad-livekit && ./run.sh

# Terminal 2 - Agent (optional)
cd jawad-livekit && source ../iterate-hack/bin/activate && python interview_agent.py dev

# Browser - Client
open client.html
```

### API Endpoints
- http://localhost:8000 - API status
- http://localhost:8000/docs - Interactive API docs
- http://localhost:8000/rooms - List rooms

### View LiveKit Cloud Dashboard
https://cloud.livekit.io → Your Project → See active rooms and participants

## Getting Help

- Check the main README.md for detailed documentation
- See LiveKit docs: https://docs.livekit.io
- Check browser console (F12) for errors
