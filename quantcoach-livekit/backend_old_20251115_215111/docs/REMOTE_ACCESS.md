# Remote Access Guide

## 🎉 Your LiveKit Interview Platform is Running!

Since you're accessing via SSH, both servers are now publicly accessible:

### Server Addresses

**Server IP:** `129.104.252.67`

- **API Server (Backend):** http://129.104.252.67:8000
- **Web Client (Frontend):** http://129.104.252.67:8080/client.html
- **API Documentation:** http://129.104.252.67:8000/docs

### Quick Test

Open this URL in your browser (on your local machine):

```
http://129.104.252.67:8080/client.html
```

### How to Test the Video Interview

1. **On your computer**, open: http://129.104.252.67:8080/client.html

2. **First participant (Interviewer)**:
   - API Server URL is pre-filled: `http://129.104.252.67:8000`
   - Leave room name blank (to create new room)
   - Select "Interviewer"
   - Enter your name
   - Click "Create/Join Room"
   - Allow camera/microphone access when prompted

3. **Second participant (Candidate)**:
   - Open the same URL in a new browser window (or incognito/private window)
   - OR: Have a friend/teammate open it on their computer
   - Copy the room name from the first window
   - Paste it into "Room Name"
   - Select "Candidate"
   - Enter a different name
   - Click "Create/Join Room"

4. **You should now see both video feeds!**

### Testing from Multiple Devices

Share this link with teammates to test:
- **Web Client:** http://129.104.252.67:8080/client.html

They can join the same room by entering the room name.

### API Endpoints (for developers)

Test the API directly:

```bash
# Health check
curl http://129.104.252.67:8000/

# Create a room
curl -X POST http://129.104.252.67:8000/rooms/create \
  -H "Content-Type: application/json" \
  -d '{"max_participants": 10}'

# List active rooms
curl http://129.104.252.67:8000/rooms
```

### Interactive API Documentation

Visit: http://129.104.252.67:8000/docs

This provides a Swagger UI where you can test all API endpoints interactively.

### Troubleshooting

**If the client doesn't load:**
- Check if port 8080 is accessible from your network
- Try accessing from the same network as the server first

**If video doesn't work:**
- Make sure you're using HTTPS or that your browser allows media access on HTTP
- Chrome/Firefox work best
- Allow camera and microphone permissions

**If you can't connect to rooms:**
- Verify API server is running: `curl http://129.104.252.67:8000/`
- Check that LiveKit Cloud credentials are correct in `.env`

### Running Services

Currently running:
- ✅ FastAPI Server (port 8000) - API backend
- ✅ HTTP Server (port 8080) - Serving client.html
- ⏸️  Agent (not started) - Optional, requires OpenAI/Deepgram keys

### Server Management

To stop servers:
```bash
# Find the processes
ps aux | grep python | grep server

# Kill by PID or use:
pkill -f "python server.py"
pkill -f "http.server"
```

To restart:
```bash
cd /users/eleves-b/2022/jawad.chemaou/M2DS/iterateHackathon/jawad-livekit
python server.py &  # API server
python -m http.server 8080 --bind 0.0.0.0 &  # Web server
```

### Security Note

These servers are publicly accessible. For production:
- Add authentication
- Use HTTPS (not HTTP)
- Implement rate limiting
- Add firewall rules
- Use proper secrets management

For this hackathon/development, it's fine as-is!

## Next Steps

1. Test the video connection with your team
2. Add OpenAI and Deepgram keys to `.env` to enable the agent
3. Start the agent: `python interview_agent.py dev`
4. Build additional features (sentiment analysis, UI improvements, etc.)

Enjoy! 🚀
