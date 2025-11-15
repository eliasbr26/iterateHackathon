# LiveKit Interview Platform

Real-time video interview platform using LiveKit Cloud. Built for the Iterate Hackathon.

## Quick Start (For Everyone)

### 1. Download the Client
Download `client-for-friends.html` from this repository.

### 2. Host Creates Room
- Open `client-for-friends.html` in browser
- Leave room name blank
- Select "Interviewer"
- Click "Join Room"
- **Copy the room name** (e.g., "interview-2024-11-15-143000")
- Share it with participants

### 3. Participants Join
- Open `client-for-friends.html` in browser
- **Paste the room name** from host
- Select "Candidate" or "Observer"
- Click "Join Room"
- Allow camera/microphone

**That's it!** Everyone will see each other on video.

## Project Structure

```
jawad-livekit/
├── client-for-friends.html    # Main client (share with team)
├── server.py                   # FastAPI backend
├── room_manager.py             # Room & token management
├── interview_agent.py          # AI agent (optional)
├── run.sh                      # Quick start script
├── README.md                   # This file
├── docs/                       # Additional documentation
└── archive/                    # Old versions
```

## For Developers

### Backend API

The backend provides REST API for room management:

```bash
# Start API server
python server.py

# Or use the script
./run.sh
```

**Endpoints:**
- `POST /rooms/create` - Create new room
- `POST /tokens/generate` - Generate access token
- `GET /rooms` - List active rooms
- `GET /rooms/{name}/participants` - Get participants

API docs: http://localhost:8000/docs

### AI Agent (Optional)

The agent transcribes conversations in real-time. Requires:
- OpenAI API key
- Deepgram API key

```bash
# Add keys to .env file
OPENAI_API_KEY=your-key
DEEPGRAM_API_KEY=your-key

# Run agent
python interview_agent.py dev
```

### LiveKit Configuration

Connected to: `wss://iterate-hackathon-1qxzyt73.livekit.cloud`

Credentials are in `../.env`:
```
LIVEKIT_URL=wss://iterate-hackathon-1qxzyt73.livekit.cloud
LIVEKIT_API_KEY=your-key
LIVEKIT_API_SECRET=your-secret
```

## How It Works

```
┌─────────────┐         ┌─────────────┐
│ Interviewer │◄───────►│  LiveKit    │
└─────────────┘   Video  │   Cloud     │
                  Audio  │             │
┌─────────────┐         │             │
│  Candidate  │◄───────►│             │
└─────────────┘         └─────────────┘
       │                       │
       │                       │
       └───────────────────────┘
           All connected via
           WebRTC (peer-to-peer)
```

## Features

✅ Real-time video/audio
✅ Multiple participants
✅ No backend required for basic usage
✅ Works from anywhere with internet
✅ LiveKit Cloud dashboard monitoring
✅ Optional AI transcription

## Deployment

### For Local Testing
Use SSH port forwarding:
```bash
ssh -L 8000:localhost:8000 -L 8080:localhost:8080 user@server
```

### For Production
- Use ngrok or cloudflare tunnel
- Or deploy backend to cloud (Heroku, Railway, etc.)
- Share the public URL

See `docs/` for detailed deployment guides.

## Troubleshooting

**Can't see video?**
- Allow camera/microphone permissions
- Use Chrome or Firefox
- Check room name is exactly the same

**Connection issues?**
- Check internet connection
- Try different browser
- Open browser console (F12) for errors

**No one else appears?**
- Verify everyone used the same room name
- Check LiveKit dashboard for active participants
- Refresh the page and try again

## Documentation

- `docs/QUICKSTART.md` - Detailed setup guide
- `docs/SHARE_WITH_FRIENDS.md` - Deployment options
- `docs/SSH_ACCESS.md` - SSH tunneling guide

## Team Roles

This platform was built to support 5 team roles:

1. **LiveKit Integration** ✅ - Complete
2. **Frontend UI** - Enhance client interface
3. **Backend/Database** - Add persistence, analytics
4. **ML/Analysis** - Sentiment analysis, scoring
5. **DevOps** - Deployment, monitoring

## Next Steps

- [ ] Add sentiment analysis to agent
- [ ] Build React/Vue frontend
- [ ] Add interview recording
- [ ] Create evaluation metrics
- [ ] Deploy to production

## License

MIT

## Contact

For issues or questions, check the docs/ folder or contact the team.
