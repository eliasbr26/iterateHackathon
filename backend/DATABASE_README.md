# Database Foundation - Phase 1 Complete ✅

## Overview

This document describes the comprehensive database schema implemented to support all 7 pillars of the QuantCoach AI Hiring Intelligence Platform.

---

## Architecture

### Technology Stack
- **ORM**: SQLAlchemy 2.0+
- **Migration Tool**: Alembic 1.12+
- **Default Database**: SQLite (for development)
- **Production Ready**: PostgreSQL (configurable via DATABASE_URL)

### Directory Structure
```
backend/
├── database/
│   ├── __init__.py      # Package exports
│   ├── models.py        # SQLAlchemy models (15 tables)
│   ├── db.py            # Database connection & session management
│   └── crud.py          # CRUD helper functions
├── init_db.py           # Database initialization script
└── server.py            # FastAPI server (database integrated)
```

---

## Database Schema (15 Tables)

### Core Entities

#### 1. **candidates** (PILLAR 6)
Stores candidate master records with AI-generated profiles.

**Key Fields:**
- Basic info: email, name, phone
- CV data: cv_text, cv_url, cv_parsed_data
- Pre-interview profile: bio, career_summary, skill_graph, experience_matrix
- Post-interview: overall_hiring_recommendation, culture_fit_analysis, future_seniority_prediction

#### 2. **interviewers** (PILLAR 5)
Stores interviewer master records with performance tracking.

**Key Fields:**
- Basic info: email, name, role
- Historical performance: avg_fairness_score, avg_professionalism_score, avg_bias_score
- Calibration: calibration_factor, tends_harsh, tends_lenient

#### 3. **interviews**
Central entity connecting all interview data.

**Key Fields:**
- Session info: room_name, livekit_room_sid, status
- Participants: candidate_id, interviewer_id
- Job info: job_title, job_description, role_requirements
- Timing: scheduled_start, actual_start, actual_end, duration_minutes
- Live tracking: topic_coverage, time_allocation, pacing_status
- Fit analysis: role_fit_percentage, skill_gaps

---

### Transcript & Analysis

#### 4. **transcripts** (PILLAR 1)
Real-time transcription records with speaker labels.

**Key Fields:**
- timestamp, speaker (enum: interviewer/candidate/agent), text, turn_number
- Analysis flags: contains_buzzwords, is_vague, is_quantified

#### 5. **evaluations** (PILLAR 2)
LLM-powered evaluation results from Claude.

**Key Fields:**
- Window info: window_start, window_end, transcripts_evaluated
- Core evaluation: subject_relevance, question_difficulty, interviewer_tone
- Analysis: summary, key_topics, flags
- Confidence scores: confidence_subject, confidence_difficulty, confidence_tone

#### 6. **competency_scores** (PILLAR 2.1)
Detailed competency scoring (leadership, technical, communication, etc.).

**Key Fields:**
- competency (enum: 10 types)
- Scoring dimensions: overall_score, depth_score, clarity_score, relevance_score, evidence_score
- evidence_quotes, reasoning

#### 7. **star_analyses** (PILLAR 2.2)
STAR method evaluation for behavioral answers.

**Key Fields:**
- question, answer, timestamp
- STAR components: has_situation, has_task, has_action, has_result
- STAR details: situation_text, task_text, action_text, result_text
- star_completion_percentage, result_quantified, quality_rating

---

### Interviewer Performance

#### 8. **interviewer_metrics** (PILLAR 5)
Interviewer evaluation metrics (bias, fairness, professionalism).

**Key Fields:**
- Bias detection: interrupt_count, tone_changes, detected_biases
- Scores: fairness_score, professionalism_score, value_alignment_score
- Feedback: strengths, improvement_areas, coaching_tips

---

### Live Interview Support

#### 9. **red_flags** (PILLAR 1 & 2)
Real-time red flags and alerts.

**Key Fields:**
- timestamp, flag_type, severity (enum: info/warning/critical)
- description, context, transcript_id

#### 10. **follow_up_suggestions** (PILLAR 1.2)
Real-time follow-up question suggestions.

**Key Fields:**
- timestamp, suggestion, category, priority (1-5)
- context, related_competency
- Status: displayed_to_interviewer, was_followed

---

### Advanced Tools

#### 11. **contradictions** (PILLAR 4.1)
Detected contradictions in candidate responses.

**Key Fields:**
- contradiction_type (answer_to_answer, cv_to_answer, etc.)
- statement_1, statement_2 with timestamps
- severity, explanation

#### 12. **evidence_entries** (PILLAR 4.3)
Extracted evidence for specific competencies.

**Key Fields:**
- competency, evidence_type (ownership, leadership, metrics)
- quote, timestamp, context
- strength (weak/moderate/strong), is_quantified

---

### Automation

#### 13. **interview_summaries** (PILLAR 3)
Auto-generated summaries and reports.

**Key Fields:**
- summary_type (bullet_summary, full_report, ats_summary)
- title, content
- Structured data: strengths, weaknesses, highlights, next_steps
- Export status: exported_to_ats, ats_name, exported_at

---

### Candidate Profiles

#### 14. **candidate_profiles** (PILLAR 6)
Time-based candidate profile snapshots (before/during/after).

**Key Fields:**
- profile_type (pre_interview, live, post_interview)
- snapshot_timestamp, profile_data
- changes_from_previous

---

## Enums

```python
InterviewStatus: SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
SpeakerRole: INTERVIEWER, CANDIDATE, AGENT, UNKNOWN
SubjectRelevance: ON_TOPIC, PARTIALLY_RELEVANT, OFF_TOPIC, UNKNOWN
QuestionDifficulty: EASY, MEDIUM, HARD, UNKNOWN
InterviewerTone: HARSH, NEUTRAL, ENCOURAGING, UNKNOWN
RedFlagSeverity: INFO, WARNING, CRITICAL
CompetencyType: LEADERSHIP, COMMUNICATION, TECHNICAL_DEPTH, PROBLEM_SOLVING, OWNERSHIP, ADAPTABILITY, STRATEGIC_THINKING, CREATIVITY, TEAMWORK, CULTURE_FIT
```

---

## CRUD Operations (database/crud.py)

### Candidate Operations
- `create_candidate()` - Create new candidate
- `get_candidate_by_email()` - Find by email
- `get_candidate_by_id()` - Find by ID
- `update_candidate_profile()` - Update profile data

### Interviewer Operations
- `create_interviewer()` - Create new interviewer
- `get_interviewer_by_email()` - Find by email
- `get_or_create_interviewer()` - Get existing or create new

### Interview Operations
- `create_interview()` - Create interview session
- `get_interview_by_room_name()` - Find by room name
- `start_interview()` - Mark as in progress
- `end_interview()` - Mark as completed, calculate duration
- `get_candidate_interviews()` - Get all interviews for candidate

### Transcript Operations
- `create_transcript()` - Add transcript entry
- `get_interview_transcripts()` - Get all transcripts for interview

### Evaluation Operations
- `create_evaluation()` - Create evaluation record
- `get_interview_evaluations()` - Get all evaluations

### Competency Scores
- `create_competency_score()` - Add competency score
- `get_competency_scores()` - Get all scores for interview

### Red Flags
- `create_red_flag()` - Create red flag alert
- `get_interview_red_flags()` - Get all red flags

### Follow-Up Suggestions
- `create_follow_up_suggestion()` - Add suggestion
- `get_pending_suggestions()` - Get undisplayed suggestions

### Summaries
- `create_interview_summary()` - Generate summary

### Utilities
- `get_interview_statistics()` - Get comprehensive stats

---

## Database Initialization

### Command Line Usage

```bash
# Initialize database (create all tables)
python init_db.py

# Check database health
python init_db.py --check

# Show table statistics
python init_db.py --stats

# Reset database (WARNING: deletes all data!)
python init_db.py --reset
```

### Programmatic Usage

```python
from database import init_db, get_db_context, crud

# Initialize database
init_db()

# Use database
with get_db_context() as db:
    # Create candidate
    candidate = crud.create_candidate(
        db=db,
        email="john@example.com",
        name="John Doe",
        cv_text="Experienced software engineer..."
    )

    # Create interview
    interview = crud.create_interview(
        db=db,
        room_name="interview-2025-01-01",
        candidate_id=candidate.id,
        job_title="Senior Engineer"
    )

    # Start interview
    crud.start_interview(db, interview.id)
```

---

## Configuration

### Environment Variables

```bash
# Database URL (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./quantcoach_interviews.db

# For PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/quantcoach
```

### FastAPI Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from database import get_db, crud

@app.post("/candidates")
async def create_candidate_endpoint(
    email: str,
    name: str,
    db: Session = Depends(get_db)
):
    candidate = crud.create_candidate(db, email=email, name=name)
    return candidate
```

---

## Integration with Existing System

### Server Startup
The database is automatically initialized when `server.py` starts:

```python
@app.on_event("startup")
async def startup_event():
    logger.info("📦 Initializing database...")
    init_db()
    logger.info("✅ Database initialized successfully")
```

### Hybrid Storage Strategy
Currently implemented with **hybrid storage**:
- **In-memory** (defaultdict): For real-time SSE streaming (low latency)
- **Database**: For persistence and analytics (durable storage)

Future: Migrate to **database-only** storage for true persistence.

---

## Testing

### Manual Testing

```bash
# 1. Initialize database
cd backend
python init_db.py

# 2. Start server
python server.py

# 3. Check health
curl http://localhost:8000/health

# 4. Check database stats
python init_db.py --stats
```

### Automated Testing

```python
import pytest
from database import init_db, get_db_context, crud

def test_create_candidate():
    init_db()
    with get_db_context() as db:
        candidate = crud.create_candidate(
            db=db,
            email="test@example.com",
            name="Test User"
        )
        assert candidate.id is not None
        assert candidate.email == "test@example.com"
```

---

## Next Steps

### Immediate (Phase 1 Complete)
- ✅ Database schema designed
- ✅ SQLAlchemy models created
- ✅ CRUD operations implemented
- ✅ Database initialization integrated into server.py
- ⏳ **TODO**: Migrate `/rooms/create` to store interviews in database
- ⏳ **TODO**: Migrate event callbacks to save transcripts/evaluations to database
- ⏳ **TODO**: Update SSE stream to fetch from database

### Phase 2: Enhanced Evaluation (PILLAR 2 & 6)
- Implement competency scoring engine
- Implement STAR analysis engine
- Implement bluffing detector
- Implement CV parser for candidate profiles

### Phase 3: Live Co-Pilot (PILLAR 1 & 5)
- Implement follow-up suggestion engine
- Implement coverage tracker
- Implement interviewer bias detector

### Phase 4-7: Automation, Tools, RAG
- Continue implementation of remaining pillars

---

## Database Schema Diagram

```
┌────────────────┐
│   candidates   │◄─────┐
└────────────────┘      │
                        │
┌────────────────┐      │
│  interviewers  │◄─┐   │
└────────────────┘  │   │
                    │   │
              ┌─────┴───┴──────┐
              │   interviews   │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
   │transcripts│   │evaluations│   │red_flags│
   └──────────┘   └────┬─────┘   └─────────┘
                       │
            ┌──────────┼──────────┐
            │          │          │
      ┌─────▼──┐  ┌───▼────┐  ┌─▼─────┐
      │competency│  │star_   │  │summaries│
      │_scores  │  │analyses│  └─────────┘
      └─────────┘  └────────┘
```

---

## Support & Documentation

- **Database Models**: `backend/database/models.py`
- **CRUD Operations**: `backend/database/crud.py`
- **Initialization**: `backend/init_db.py`
- **Server Integration**: `backend/server.py`

For questions, check the inline documentation in each file.

---

**Last Updated**: Phase 1 Complete - Database Foundation Ready
**Status**: ✅ Production Ready for SQLite, PostgreSQL
