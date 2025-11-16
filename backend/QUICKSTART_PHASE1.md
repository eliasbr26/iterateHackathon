# ✅ Phase 1 Complete - Quick Start Guide

## What Was Fixed

Fixed LiveKit API import error by:
1. Installing `livekit-api` package
2. Installing all dependencies from `requirements.txt`
3. Updating imports in `room_manager.py`

## System Status

### ✅ Database Foundation
- **14 tables created** supporting all 7 pillars
- **SQLite database**: `quantcoach_interviews.db`
- **CRUD operations** implemented
- **Database auto-initializes** on server startup

### ✅ Server Configuration
- **RoomManager** initialized successfully
- **AgentManager** initialized successfully
- **Database** initialized automatically
- **All imports** working correctly

---

## How to Run

### 1. Start the Backend Server

```bash
cd quantcoach-livekit/backend
python server.py
```

You should see:
```
📦 Using SQLite database: sqlite:///./quantcoach_interviews.db
✅ RoomManager initialized
✅ AgentManager initialized successfully
🚀 Starting QuantCoach LiveKit API...
📦 Initializing database...
✅ Database initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Start the Frontend

In a new terminal:

```bash
cd quantcoach-livekit/frontend
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## Database Commands

```bash
# Check database statistics
python init_db.py --stats

# Check database health
python init_db.py --check

# Reset database (WARNING: deletes all data!)
python init_db.py --reset
```

---

## API Endpoints Available

### Room Management
- `POST /rooms/create` - Create interview room
- `GET /rooms` - List all rooms
- `GET /rooms/{room_name}/participants` - Get participants
- `DELETE /rooms/{room_name}` - Delete room

### Real-time Data
- `GET /rooms/{room_name}/stream` - SSE stream (transcripts + evaluations)
- `GET /rooms/{room_name}/analytics` - Aggregated analytics
- `GET /rooms/{room_name}/status` - Agent status

### Tokens
- `POST /tokens/generate` - Generate access token

---

## Environment Variables

Make sure your `.env` file has:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://iterate-hackathon-1qxzyt73.livekit.cloud
LIVEKIT_API_KEY=APIgvNeqnUXX3y9
LIVEKIT_API_SECRET=XqU85wFfZwxVHUZU7hgkzbBOfaGNL4l1xChephaYL9XB

# AI APIs
ELEVENLABS_API_KEY=sk_6b30b9a41e477733c0e8e9726645c38aafbb7deef8dd0beb
ANTHROPIC_API_KEY=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

# Optional Database (defaults to SQLite)
# DATABASE_URL=postgresql://user:password@localhost/quantcoach
```

---

## Database Schema (14 Tables)

All tables are ready to support the 7 pillars:

| Table | Records | Pillar |
|-------|---------|--------|
| candidates | 0 | 6 |
| interviewers | 0 | 5 |
| interviews | 0 | All |
| transcripts | 0 | 1 |
| evaluations | 0 | 2 |
| competency_scores | 0 | 2 |
| star_analyses | 0 | 2 |
| interviewer_metrics | 0 | 5 |
| red_flags | 0 | 1, 2 |
| follow_up_suggestions | 0 | 1 |
| contradictions | 0 | 4 |
| evidence_entries | 0 | 4 |
| interview_summaries | 0 | 3 |
| candidate_profiles | 0 | 6 |

---

## Testing the System

### Test 1: Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "livekit_url": "wss://iterate-hackathon-1qxzyt73.livekit.cloud",
  "timestamp": "2025-11-16T..."
}
```

### Test 2: Create a Room
```bash
curl -X POST http://localhost:8000/rooms/create \
  -H "Content-Type: application/json" \
  -d '{"room_name": "test-interview-001"}'
```

### Test 3: List Rooms
```bash
curl http://localhost:8000/rooms
```

### Test 4: Check Database
```bash
python init_db.py --stats
```

You should see interview data in the database!

---

## What's Next?

Phase 1 is complete! You now have:
- ✅ Database foundation (all 7 pillars supported)
- ✅ Server running with database integration
- ✅ All imports working correctly
- ✅ Room management functional

### Ready for Phase 2?

Choose which pillar to implement next:

1. **PILLAR 2**: Enhanced Candidate Evaluation & Scoring
   - Competency scoring engine
   - STAR analysis engine
   - Bluffing detector
   - Cultural fit analyzer

2. **PILLAR 6**: AI-Generated Candidate Profiles
   - CV parser
   - Pre-interview profile generator
   - Live profile updates
   - Post-interview enrichment

3. **PILLAR 1**: Live Interview Co-Pilot
   - Smart follow-up suggestions
   - Topic coverage tracker
   - Interview flow manager
   - Dynamic script recommendations

4. **PILLAR 5**: Interviewer Evaluation & Bias Detection
   - Bias detection engine
   - Fairness scoring
   - Professionalism metrics
   - Interviewer feedback

---

## Troubleshooting

### Server won't start
```bash
# Check if packages are installed
pip install -r requirements.txt

# Check if database is healthy
python init_db.py --check
```

### Import errors
```bash
# Reinstall all requirements
pip install -r requirements.txt --force-reinstall
```

### Database issues
```bash
# Reset database
python init_db.py --reset
```

---

**Status**: ✅ Phase 1 Complete - System Ready
**Last Updated**: 2025-11-16
