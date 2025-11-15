# Quick Start Guide - QuantCoach Backend

## 🚀 Launch in 3 Steps

### Step 1: Activate Conda Environment
```bash
conda activate ttk
```

### Step 2: Install Dependencies (first time only)
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Start the Server
```bash
python server.py
```

The server will start on **http://localhost:8000**

---

## ✅ Verify Everything Works

### Check 1: Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "livekit_url": "wss://iterate-hackathon-1qxzyt73.livekit.cloud",
  "timestamp": "2024-11-15T..."
}
```

### Check 2: API Documentation
Open in browser: http://localhost:8000/docs

You should see the interactive Swagger UI with all endpoints.

### Check 3: Create Test Room
```bash
curl -X POST http://localhost:8000/rooms/create \
  -H "Content-Type: application/json" \
  -d '{"room_name": "test-room", "max_participants": 10}'
```

Expected response with tokens for interviewer, candidate, and agent.

---

## 🎯 Common Commands

### Run Example Script
```bash
python example_usage.py
```

### List Active Rooms
```bash
curl http://localhost:8000/rooms
```

### Check Server Logs
The server outputs colored logs with emojis:
- ✅ = Success
- ❌ = Error
- ⚠️ = Warning
- 🔌 = Connection
- 🎤 = Audio

---

## 🐛 Troubleshooting

### "ModuleNotFoundError"
→ Make sure conda environment is activated: `conda activate ttk`
→ Reinstall dependencies: `pip install -r requirements.txt`

### "LiveKit not configured"
→ Check that `.env` file exists in `backend/` directory
→ Verify LiveKit credentials are correct

### "Port already in use"
→ Kill existing server: `pkill -f "python server.py"`
→ Or change port in `.env`: `PORT=8001`

---

## 📚 Next Steps

1. **Frontend Integration**: Start the full platform with `./start.sh` from root
2. **Test Video**: Connect via frontend to test video/audio calls
3. **Audio Transcription**: Join a room and speak to see real-time transcripts
4. **LLM Evaluation**: Integrate transcript buffer with Claude/GPT

---

## 🔗 Useful Links

- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Full README: [README.md](README.md)
- Complete Guide: [BACKEND_RECONSTRUCTION_COMPLETE.md](../BACKEND_RECONSTRUCTION_COMPLETE.md)

---

**Ready to go! 🎉**
