"""
FastAPI Server for QuantCoach LiveKit Interview Platform

Provides REST API endpoints for:
- Creating interview rooms
- Generating access tokens
- Managing participants
- Health checks

Compatible with the QuantCoach frontend VideoArea component.
"""

import asyncio
import io
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from room_manager import RoomManager
from agent_manager import AgentManager
from database import init_db, get_db, crud, InterviewStatus, SpeakerRole, CompetencyType
from evaluators import CompetencyEvaluator, STARAnalyzer, BluffingDetector, CulturalFitAnalyzer
from profiles import CVParser
from copilot import FollowUpSuggester, CoverageTracker, QualityScorer
from question_bank import QuestionGenerator, DifficultyCalibrator, QuestionSelector
from interviewer_feedback import PacingMonitor, ToneAnalyzer, QuestionQualityChecker, BiasDetector
from reporting import SummaryGenerator, ReportBuilder, ExportFormatter
from rag_engine import VectorStore, DocumentIndexer, ConversationalAssistant

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="QuantCoach LiveKit API",
    description="API for managing LiveKit interview rooms with audio transcription",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Initialize RoomManager
try:
    room_manager = RoomManager()
    logger.info("✅ RoomManager initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize RoomManager: {e}")
    logger.error("Make sure LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET are set in .env")
    room_manager = None

# Initialize AgentManager
agent_manager = None
if room_manager:
    try:
        livekit_url = os.getenv("LIVEKIT_URL")
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not elevenlabs_api_key:
            logger.warning("⚠️ ELEVENLABS_API_KEY not set - transcription will not work")
        if not anthropic_api_key:
            logger.warning("⚠️ ANTHROPIC_API_KEY not set - evaluation will not work")

        agent_manager = AgentManager(
            livekit_url=livekit_url,
            elevenlabs_api_key=elevenlabs_api_key or "",
            anthropic_api_key=anthropic_api_key or "",
            output_dir="transcripts"
        )
        logger.info("✅ AgentManager initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize AgentManager: {e}")
        agent_manager = None

# Initialize Phase 2 evaluators
competency_evaluator = None
star_analyzer = None
bluffing_detector = None
cultural_fit_analyzer = None
cv_parser = None

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_api_key:
    try:
        competency_evaluator = CompetencyEvaluator(api_key=anthropic_api_key)
        star_analyzer = STARAnalyzer(api_key=anthropic_api_key)
        bluffing_detector = BluffingDetector(api_key=anthropic_api_key)
        cultural_fit_analyzer = CulturalFitAnalyzer(api_key=anthropic_api_key)
        cv_parser = CVParser(api_key=anthropic_api_key)
        logger.info("✅ Phase 2 evaluators initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Phase 2 evaluators: {e}")
else:
    logger.warning("⚠️ ANTHROPIC_API_KEY not set - Phase 2 evaluators will not be available")

# Initialize PILLAR 1 Co-Pilot modules
followup_suggester = None
if anthropic_api_key:
    try:
        followup_suggester = FollowUpSuggester(api_key=anthropic_api_key)
        logger.info("✅ PILLAR 1 Co-Pilot initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PILLAR 1 Co-Pilot: {e}")

# Initialize PILLAR 3 Question Bank modules
question_generator = None
if anthropic_api_key:
    try:
        question_generator = QuestionGenerator(api_key=anthropic_api_key)
        logger.info("✅ PILLAR 3 Question Bank initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PILLAR 3 Question Bank: {e}")

# Initialize PILLAR 4 Interviewer Feedback modules
tone_analyzer = None
quality_checker = None
bias_detector = None
if anthropic_api_key:
    try:
        tone_analyzer = ToneAnalyzer(api_key=anthropic_api_key)
        quality_checker = QuestionQualityChecker(api_key=anthropic_api_key)
        bias_detector = BiasDetector(api_key=anthropic_api_key)
        logger.info("✅ PILLAR 4 Interviewer Feedback initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PILLAR 4 Interviewer Feedback: {e}")

# Initialize PILLAR 5 Post-Interview Analysis & Reporting modules
summary_generator = None
report_builder = None
export_formatter = None
if anthropic_api_key:
    try:
        summary_generator = SummaryGenerator(api_key=anthropic_api_key)
        report_builder = ReportBuilder()
        export_formatter = ExportFormatter()
        logger.info("✅ PILLAR 5 Post-Interview Analysis & Reporting initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PILLAR 5 Reporting: {e}")

# Initialize PILLAR 7 RAG Conversational Q&A Engine
vector_store = None
conversational_assistant = None
openai_api_key = os.getenv("OPENAI_API_KEY")
if anthropic_api_key and openai_api_key:
    try:
        vector_store = VectorStore(persist_directory="./chroma_db")
        conversational_assistant = ConversationalAssistant(
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key,
            vector_store=vector_store
        )
        logger.info("✅ PILLAR 7 RAG Conversational Q&A Engine initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize PILLAR 7 RAG Engine: {e}")
else:
    if not openai_api_key:
        logger.warning("⚠️ OPENAI_API_KEY not set - RAG Q&A will not be available")

# Coverage trackers and quality scorers per interview (room_name -> tracker/scorer)
coverage_trackers: Dict[str, CoverageTracker] = {}
quality_scorers: Dict[str, QualityScorer] = {}

# Question bank components per interview (room_name -> calibrator/selector)
difficulty_calibrators: Dict[str, DifficultyCalibrator] = {}
question_selectors: Dict[str, QuestionSelector] = {}

# Interviewer feedback components per interview (room_name -> pacing_monitor)
pacing_monitors: Dict[str, PacingMonitor] = {}

# Event queues for SSE streaming: room_name -> asyncio.Queue
event_queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)

# Session data storage: room_name -> {transcripts: [], evaluations: []}
session_data: Dict[str, dict] = defaultdict(lambda: {"transcripts": [], "evaluations": []})


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        logger.info("🚀 Starting QuantCoach LiveKit API...")

        # Initialize database
        logger.info("📦 Initializing database...")
        init_db()
        logger.info("✅ Database initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue anyway - application can still work with in-memory storage


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if agent_manager:
        await agent_manager.cleanup()


# Pydantic models for request/response
class CreateRoomRequest(BaseModel):
    room_name: Optional[str] = None
    max_participants: int = 10
    candidate_id: Optional[int] = None


class CreateRoomResponse(BaseModel):
    sid: str
    name: str
    max_participants: int
    creation_time: int
    interviewer_token: str
    candidate_token: str
    agent_token: str
    url: str
    interview_id: int


class GenerateTokenRequest(BaseModel):
    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None
    role: str = "participant"  # interviewer, candidate, agent, or participant


class GenerateTokenResponse(BaseModel):
    token: str
    room_name: str
    participant_identity: str
    url: str


class RoomInfo(BaseModel):
    sid: str
    name: str
    num_participants: int
    creation_time: int


class ParticipantInfo(BaseModel):
    sid: str
    identity: str
    name: str
    state: str


# Phase 2 - Enhanced Evaluation API Models
class ParseCVRequest(BaseModel):
    cv_text: str
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None


class ParseCVResponse(BaseModel):
    candidate_id: int
    parsed_data: Dict
    status: str


class EvaluateCompetenciesRequest(BaseModel):
    interview_id: int
    competencies: Optional[List[str]] = None  # If None, evaluates all


class CompetencyScoreResponse(BaseModel):
    competency: str
    overall_score: float
    depth_score: float
    clarity_score: float
    relevance_score: float
    evidence_score: float
    evidence_quotes: List[str]
    reasoning: str


class STARAnalysisRequest(BaseModel):
    interview_id: int
    question: str
    answer: str


class STARAnalysisResponse(BaseModel):
    has_situation: bool
    has_task: bool
    has_action: bool
    has_result: bool
    situation_text: Optional[str]
    task_text: Optional[str]
    action_text: Optional[str]
    result_text: Optional[str]
    star_completion_percentage: float
    quality_rating: str
    star_score: float


class BluffingDetectionRequest(BaseModel):
    interview_id: int


class BluffingDetectionResponse(BaseModel):
    bluffing_score: float
    risk_level: str
    red_flags: List[Dict]
    credibility_assessment: str
    specific_concerns: List[str]


class CulturalFitRequest(BaseModel):
    interview_id: int
    company_values: Optional[List[str]] = None


class CulturalFitResponse(BaseModel):
    overall_fit_score: float
    recommendation: str
    value_alignment: List[Dict]
    cultural_dimensions: Dict
    top_strengths: List[str]
    potential_concerns: List[str]


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "QuantCoach LiveKit API",
        "version": "2.0.0",
        "livekit_configured": room_manager is not None,
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured. Check LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET"
        )

    return {
        "status": "healthy",
        "livekit_url": room_manager.url,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/rooms/create", response_model=CreateRoomResponse)
async def create_interview_room(request: CreateRoomRequest):
    """
    Create a new interview room and generate tokens for all participants

    This endpoint:
    1. Creates a new LiveKit room
    2. Generates access tokens for interviewer, candidate, and agent
    3. Returns all information needed to join the room
    """
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured"
        )

    try:
        # Generate room name if not provided
        room_name = request.room_name or f"interview-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        logger.info(f"Creating room: {room_name}")

        # Create the room
        room = await room_manager.create_room(room_name, request.max_participants)

        logger.info(f"✅ Room created: {room['name']} (sid: {room['sid']})")

        # Generate tokens for all participant types
        interviewer_token = room_manager.generate_token(
            room_name=room_name,
            participant_identity=f"interviewer-{datetime.now().timestamp()}",
            participant_name="Interviewer",
            metadata='{"role": "interviewer"}',
        )

        candidate_token = room_manager.generate_token(
            room_name=room_name,
            participant_identity=f"candidate-{datetime.now().timestamp()}",
            participant_name="Candidate",
            metadata='{"role": "candidate"}',
        )

        agent_token = room_manager.generate_token(
            room_name=room_name,
            participant_identity=f"agent-{datetime.now().timestamp()}",
            participant_name="Analysis Agent",
            metadata='{"role": "agent", "type": "analyzer"}',
        )

        logger.info(f"✅ Tokens generated for room: {room_name}")

        # Create interview database record
        db = next(get_db())
        try:
            interview = crud.create_interview(
                db=db,
                room_name=room_name,
                candidate_id=request.candidate_id,
                livekit_room_sid=room["sid"],
            )
            logger.info(f"✅ Created interview record {interview.id} for room: {room_name}")
        except Exception as e:
            logger.error(f"⚠️ Failed to create interview record: {e}")
            # Continue anyway - the room was created successfully
            interview = None
        finally:
            db.close()

        # Auto-start agent if AgentManager is available
        if agent_manager:
            async def event_callback(event: dict):
                """Callback to publish events to SSE streams"""
                event_type = event.get("type")
                event_data = event.get("data")

                # Store events in session data
                if event_type == "transcript":
                    session_data[room_name]["transcripts"].append(event_data)
                elif event_type == "evaluation":
                    session_data[room_name]["evaluations"].append(event_data)

                # Publish to all subscribers
                if room_name in event_queues:
                    for queue in event_queues[room_name]:
                        try:
                            await queue.put(event)
                        except Exception:
                            pass  # Queue might be closed

            # Start agent
            agent_started = await agent_manager.start_agent(
                room_name=room_name,
                livekit_token=agent_token,
                event_callback=event_callback
            )

            if agent_started:
                logger.info(f"✅ Agent auto-started for room: {room_name}")
            else:
                logger.warning(f"⚠️ Failed to auto-start agent for room: {room_name}")

        return CreateRoomResponse(
            sid=room["sid"],
            name=room["name"],
            max_participants=room["max_participants"],
            creation_time=room["creation_time"],
            interviewer_token=interviewer_token,
            candidate_token=candidate_token,
            agent_token=agent_token,
            url=room_manager.url,
            interview_id=interview.id if interview else 0,
        )

    except Exception as e:
        logger.error(f"❌ Failed to create room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tokens/generate", response_model=GenerateTokenResponse)
async def generate_token(request: GenerateTokenRequest):
    """
    Generate an access token for a participant to join an existing room

    This is used when a participant wants to join a room that already exists.
    """
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured"
        )

    try:
        logger.info(f"Generating token for {request.participant_identity} in room {request.room_name}")

        token = room_manager.generate_token(
            room_name=request.room_name,
            participant_identity=request.participant_identity,
            participant_name=request.participant_name,
            metadata=f'{{"role": "{request.role}"}}',
        )

        logger.info(f"✅ Token generated for {request.participant_identity}")

        return GenerateTokenResponse(
            token=token,
            room_name=request.room_name,
            participant_identity=request.participant_identity,
            url=room_manager.url,
        )

    except Exception as e:
        logger.error(f"❌ Failed to generate token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms", response_model=list[RoomInfo])
async def list_rooms():
    """
    List all active rooms
    """
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured"
        )

    try:
        rooms = await room_manager.list_rooms()
        logger.info(f"Listed {len(rooms)} active rooms")
        return [
            RoomInfo(
                sid=room["sid"],
                name=room["name"],
                num_participants=room["num_participants"],
                creation_time=room["creation_time"],
            )
            for room in rooms
        ]
    except Exception as e:
        logger.error(f"❌ Failed to list rooms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms/{room_name}/participants", response_model=list[ParticipantInfo])
async def get_room_participants(room_name: str):
    """
    Get list of participants in a specific room
    """
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured"
        )

    try:
        participants = await room_manager.get_room_participants(room_name)
        logger.info(f"Room {room_name} has {len(participants)} participants")
        return [
            ParticipantInfo(
                sid=p["sid"],
                identity=p["identity"],
                name=p["name"],
                state=p["state"],
            )
            for p in participants
        ]
    except Exception as e:
        logger.error(f"❌ Failed to get participants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/rooms/{room_name}")
async def delete_room(room_name: str):
    """
    Delete a room
    """
    if not room_manager:
        raise HTTPException(
            status_code=503,
            detail="LiveKit not configured"
        )

    try:
        # Stop agent if running
        if agent_manager:
            await agent_manager.stop_agent(room_name)

        await room_manager.delete_room(room_name)
        logger.info(f"✅ Room deleted: {room_name}")
        return {"status": "success", "message": f"Room {room_name} deleted"}
    except Exception as e:
        logger.error(f"❌ Failed to delete room: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms/{room_name}/stream")
async def stream_room_events(room_name: str):
    """
    Server-Sent Events stream for real-time transcripts and evaluations

    Streams:
    - transcript events: {type: "transcript", data: {...}}
    - evaluation events: {type: "evaluation", data: {...}}
    - status events: {type: "status", data: {...}}
    """
    # Create a new queue for this client
    client_queue = asyncio.Queue()
    event_queues[room_name].append(client_queue)

    logger.info(f"📡 New SSE client connected to room: {room_name}")

    async def event_generator():
        try:
            # Send connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({
                    "room": room_name,
                    "timestamp": datetime.now().isoformat()
                })
            }

            # Send any existing data
            if room_name in session_data:
                data = session_data[room_name]

                # Send existing transcripts
                for transcript in data["transcripts"]:
                    yield {
                        "event": "transcript",
                        "data": json.dumps(transcript)
                    }

                # Send existing evaluations
                for evaluation in data["evaluations"]:
                    yield {
                        "event": "evaluation",
                        "data": json.dumps(evaluation)
                    }

            # Stream new events
            while True:
                event = await client_queue.get()

                if event is None:  # Sentinel to stop
                    break

                event_type = event.get("type", "message")
                event_data = event.get("data", {})

                yield {
                    "event": event_type,
                    "data": json.dumps(event_data)
                }

        except asyncio.CancelledError:
            logger.info(f"📡 SSE client disconnected from room: {room_name}")
        finally:
            # Remove queue from subscribers
            if room_name in event_queues:
                event_queues[room_name].remove(client_queue)
                if not event_queues[room_name]:
                    del event_queues[room_name]

    return EventSourceResponse(event_generator())


@app.get("/rooms/{room_name}/analytics")
async def get_room_analytics(room_name: str):
    """
    Get aggregated analytics for a room

    Returns:
    - Difficulty distribution (easy/medium/hard percentages)
    - Topic coverage (which topics discussed)
    - Average tone
    - Red flag count
    - Confidence scores
    """
    if room_name not in session_data:
        raise HTTPException(
            status_code=404,
            detail=f"No session data found for room: {room_name}"
        )

    data = session_data[room_name]
    evaluations = data["evaluations"]

    if not evaluations:
        return {
            "room": room_name,
            "total_evaluations": 0,
            "difficulty_distribution": {},
            "topic_coverage": {},
            "average_tone": None,
            "red_flag_count": 0,
            "average_confidence": {}
        }

    # Calculate difficulty distribution
    difficulty_counts = {"easy": 0, "medium": 0, "hard": 0, "unknown": 0}
    for eval in evaluations:
        difficulty = eval.get("question_difficulty", "unknown").lower()
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

    total = len(evaluations)
    difficulty_distribution = {
        k: (v / total * 100) if total > 0 else 0
        for k, v in difficulty_counts.items()
    }

    # Calculate topic coverage
    all_topics = [
        "CV_TECHNIQUES", "REGULARIZATION", "FEATURE_SELECTION",
        "STATIONARITY", "TIME_SERIES_MODELS", "OPTIMIZATION_PYTHON",
        "LOOKAHEAD_BIAS", "DATA_PIPELINE", "BEHAVIORAL_PRESSURE",
        "BEHAVIORAL_TEAMWORK", "EXTRA"
    ]

    topics_covered = set()
    for eval in evaluations:
        topics = eval.get("key_topics", [])
        topics_covered.update(topics)

    topic_coverage = {
        topic: topic in topics_covered
        for topic in all_topics
    }

    # Calculate average tone
    tone_values = {"harsh": 0, "neutral": 1, "encouraging": 2}
    tone_scores = []
    for eval in evaluations:
        tone = eval.get("interviewer_tone", "neutral").lower()
        if tone in tone_values:
            tone_scores.append(tone_values[tone])

    avg_tone_score = sum(tone_scores) / len(tone_scores) if tone_scores else 1
    avg_tone = "neutral"
    if avg_tone_score < 0.5:
        avg_tone = "harsh"
    elif avg_tone_score > 1.5:
        avg_tone = "encouraging"

    # Count red flags
    red_flag_count = 0
    for eval in evaluations:
        flags = eval.get("flags", [])
        red_flag_count += len(flags)

        # Count off-topic as red flag
        if eval.get("subject_relevance") == "off_topic":
            red_flag_count += 1

    # Calculate average confidence
    avg_confidence = {
        "subject": sum(e.get("confidence_subject", 0) for e in evaluations) / total,
        "difficulty": sum(e.get("confidence_difficulty", 0) for e in evaluations) / total,
        "tone": sum(e.get("confidence_tone", 0) for e in evaluations) / total,
    }

    return {
        "room": room_name,
        "total_evaluations": len(evaluations),
        "total_transcripts": len(data["transcripts"]),
        "difficulty_distribution": difficulty_distribution,
        "topic_coverage": topic_coverage,
        "average_tone": avg_tone,
        "red_flag_count": red_flag_count,
        "average_confidence": avg_confidence,
        "evaluations_sample": evaluations[-5:] if len(evaluations) > 5 else evaluations
    }


@app.get("/rooms/{room_name}/status")
async def get_room_status(room_name: str):
    """Get status of agent for a room"""
    if not agent_manager:
        raise HTTPException(
            status_code=503,
            detail="AgentManager not available"
        )

    status = agent_manager.get_agent_status(room_name)

    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"No agent found for room: {room_name}"
        )

    return {
        "room": room_name,
        **status
    }


# ========================================
# PHASE 2 - ENHANCED EVALUATION ENDPOINTS
# ========================================

@app.post("/candidates/parse-cv", response_model=ParseCVResponse)
async def parse_candidate_cv(request: ParseCVRequest, db: Session = Depends(get_db)):
    """
    Parse candidate CV and create candidate profile

    PILLAR 6: AI-Generated Candidate Profiles
    Extracts structured information from CV text and stores in database
    """
    if not cv_parser:
        raise HTTPException(
            status_code=503,
            detail="CV Parser not available - check ANTHROPIC_API_KEY"
        )

    try:
        logger.info(f"📄 Parsing CV for candidate: {request.candidate_name or 'Unknown'}")

        # Parse CV
        parsed_data = await cv_parser.parse(request.cv_text)

        # Extract name and email from parsed data if not provided
        personal_info = parsed_data.get("personal_info", {})
        name = request.candidate_name or personal_info.get("name", "Unknown")
        email = request.candidate_email or personal_info.get("email")

        # Create or update candidate in database
        candidate = crud.get_candidate_by_email(db, email) if email else None

        if candidate:
            # Update existing candidate
            logger.info(f"Updating existing candidate: {candidate.id}")
            candidate = crud.update_candidate(
                db,
                candidate_id=candidate.id,
                name=name,
                email=email,
                cv_text=request.cv_text,
                cv_parsed_data=parsed_data
            )
        else:
            # Create new candidate
            logger.info(f"Creating new candidate: {name}")
            candidate = crud.create_candidate(
                db,
                name=name,
                email=email,
                cv_text=request.cv_text,
                cv_parsed_data=parsed_data
            )

        logger.info(f"✅ CV parsed and stored for candidate {candidate.id}")

        return ParseCVResponse(
            candidate_id=candidate.id,
            parsed_data=parsed_data,
            status="success"
        )

    except Exception as e:
        logger.error(f"❌ Failed to parse CV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/candidates/upload-cv")
async def upload_candidate_cv(
    file: UploadFile = File(...),
    candidate_name: Optional[str] = None,
    candidate_email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload candidate CV file and create/update candidate profile

    PILLAR 6: AI-Generated Candidate Profiles
    Accepts PDF or TXT CV files, extracts text, and creates candidate profile
    """
    if not cv_parser:
        raise HTTPException(
            status_code=503,
            detail="CV Parser not available - check ANTHROPIC_API_KEY"
        )

    try:
        logger.info(f"📤 Uploading CV file: {file.filename}")

        # Validate file type
        allowed_extensions = ['.txt', '.pdf']
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        # Read file content
        content_bytes = await file.read()

        # Extract text based on file type
        if file_ext == '.pdf':
            # Parse PDF file
            try:
                pdf_file = io.BytesIO(content_bytes)
                pdf_reader = PdfReader(pdf_file)

                # Extract text from all pages
                text_parts = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                if not text_parts:
                    raise HTTPException(
                        status_code=400,
                        detail="PDF file contains no extractable text"
                    )

                cv_text = "\n\n".join(text_parts)
                logger.info(f"📄 Extracted text from {len(pdf_reader.pages)} PDF pages")

            except Exception as e:
                logger.error(f"Failed to parse PDF: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse PDF file: {str(e)}"
                )
        else:
            # Text file
            try:
                cv_text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="File must be UTF-8 encoded text"
                )

        # Parse CV using AI
        logger.info(f"🤖 Parsing CV for candidate: {candidate_name or 'Unknown'}")
        parsed_data = await cv_parser.parse(cv_text)

        # Extract name and email from parsed data if not provided
        personal_info = parsed_data.get("personal_info", {})
        name = candidate_name or personal_info.get("name", "Unknown")
        email = candidate_email or personal_info.get("email")

        # Create or update candidate in database
        candidate = crud.get_candidate_by_email(db, email) if email else None

        if candidate:
            # Update existing candidate
            logger.info(f"Updating existing candidate: {candidate.id}")
            candidate = crud.update_candidate(
                db,
                candidate_id=candidate.id,
                name=name,
                email=email,
                cv_text=cv_text,
                cv_parsed_data=parsed_data
            )
        else:
            # Create new candidate
            logger.info(f"Creating new candidate: {name}")
            candidate = crud.create_candidate(
                db,
                name=name,
                email=email,
                cv_text=cv_text,
                cv_parsed_data=parsed_data
            )

        logger.info(f"✅ CV uploaded and parsed for candidate {candidate.id}")

        return {
            "status": "success",
            "candidate_id": candidate.id,
            "filename": file.filename,
            "parsed_data": parsed_data,
            "message": f"CV successfully uploaded for {name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload CV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates")
async def list_candidates(db: Session = Depends(get_db)):
    """
    Get list of all candidates

    PILLAR 6: AI-Generated Candidate Profiles
    Returns all candidates with basic info
    """
    try:
        candidates = crud.get_all_candidates(db)

        return {
            "candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "has_cv": bool(c.cv_text),
                    "interview_count": len(c.interviews) if hasattr(c, 'interviews') else 0,
                }
                for c in candidates
            ],
            "total": len(candidates)
        }
    except Exception as e:
        logger.error(f"❌ Failed to list candidates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/candidates/{candidate_id}")
async def get_candidate_detail(candidate_id: int, db: Session = Depends(get_db)):
    """
    Get detailed candidate profile with interviews and transcripts

    PILLAR 6: AI-Generated Candidate Profiles
    Returns full candidate info including parsed CV data and interview history
    """
    try:
        candidate = crud.get_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Get all interviews for this candidate
        interviews_data = []
        if hasattr(candidate, 'interviews'):
            for interview in candidate.interviews:
                # Get transcripts for this interview
                transcripts = crud.get_transcripts_by_interview(db, interview.id)

                # Get summary if available
                summary = crud.get_interview_summary(db, interview.id)

                interviews_data.append({
                    "id": interview.id,
                    "room_name": interview.room_name,
                    "status": interview.status,
                    "started_at": interview.actual_start.isoformat() if interview.actual_start else None,
                    "ended_at": interview.actual_end.isoformat() if interview.actual_end else None,
                    "transcript_count": len(transcripts),
                    "transcripts": [
                        {
                            "id": t.id,
                            "speaker": t.speaker,
                            "text": t.text,
                            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                        }
                        for t in transcripts
                    ],
                    "summary": {
                        "overall_assessment": summary.overall_assessment if summary else None,
                        "key_strengths": summary.key_strengths if summary else [],
                        "areas_for_improvement": summary.areas_for_improvement if summary else [],
                        "recommendation": summary.recommendation if summary else None,
                    } if summary else None
                })

        return {
            "id": candidate.id,
            "name": candidate.name,
            "email": candidate.email,
            "created_at": candidate.created_at.isoformat() if candidate.created_at else None,
            "updated_at": candidate.updated_at.isoformat() if candidate.updated_at else None,
            "cv_text": candidate.cv_text,
            "cv_parsed_data": candidate.cv_parsed_data or {},
            "interviews": interviews_data,
            "total_interviews": len(interviews_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/candidates/{candidate_id}")
async def update_candidate_profile(
    candidate_id: int,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update candidate profile with new information

    PILLAR 6: AI-Generated Candidate Profiles
    Updates candidate profile, merging new info with existing parsed data
    """
    try:
        candidate = crud.get_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Merge new data into cv_parsed_data
        current_data = candidate.cv_parsed_data or {}

        # Update top-level fields if provided
        if "name" in update_data:
            candidate.name = update_data["name"]
        if "email" in update_data:
            candidate.email = update_data["email"]

        # Merge parsed data
        if "parsed_data" in update_data:
            for key, value in update_data["parsed_data"].items():
                if isinstance(value, dict) and key in current_data:
                    # Merge dictionaries
                    current_data[key] = {**current_data[key], **value}
                else:
                    # Replace value
                    current_data[key] = value

        # Update interview notes if provided
        if "interview_notes" in update_data:
            if "interview_notes" not in current_data:
                current_data["interview_notes"] = []
            current_data["interview_notes"].append({
                "timestamp": datetime.now().isoformat(),
                "note": update_data["interview_notes"]
            })

        candidate = crud.update_candidate(
            db,
            candidate_id=candidate_id,
            name=candidate.name,
            email=candidate.email,
            cv_parsed_data=current_data
        )

        logger.info(f"✅ Updated candidate profile: {candidate.id}")

        return {
            "status": "success",
            "candidate_id": candidate.id,
            "message": "Candidate profile updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update candidate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/link-candidate/{candidate_id}")
async def link_interview_to_candidate(
    interview_id: int,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Link an interview to a candidate

    PILLAR 6: AI-Generated Candidate Profiles
    Associates an interview session with a candidate profile
    """
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        candidate = crud.get_candidate(db, candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Link interview to candidate
        interview.candidate_id = candidate_id
        db.commit()
        db.refresh(interview)

        logger.info(f"✅ Linked interview {interview_id} to candidate {candidate_id}")

        return {
            "status": "success",
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "message": f"Interview linked to {candidate.name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to link interview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/process-completion")
async def process_interview_completion(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Process interview completion and update candidate profile

    PILLAR 6: AI-Generated Candidate Profiles
    Automatically extracts insights from interview and updates candidate profile
    """
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")

        if not interview.candidate_id:
            return {
                "status": "skipped",
                "message": "Interview not linked to a candidate"
            }

        candidate = crud.get_candidate(db, interview.candidate_id)
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # Update interview status to completed
        interview.status = InterviewStatus.COMPLETED
        interview.actual_end = datetime.now()
        db.commit()
        logger.info(f"✅ Updated interview {interview_id} status to COMPLETED")

        # Get interview transcripts from database
        transcripts = crud.get_interview_transcripts(db, interview_id)

        # If no transcripts in DB, try to read from transcript files
        if not transcripts:
            transcript_dir = Path("transcripts")
            if transcript_dir.exists():
                # Find the most recent transcript folder for this room
                room_folders = list(transcript_dir.glob(f"{interview.room_name}_*"))
                if room_folders:
                    # Sort by modification time and get the most recent
                    latest_folder = max(room_folders, key=lambda p: p.stat().st_mtime)
                    transcript_file = latest_folder / "transcripts.json"

                    if transcript_file.exists():
                        try:
                            with open(transcript_file, 'r') as f:
                                data = json.load(f)
                                file_transcripts = data.get('transcripts', [])
                                logger.info(f"📄 Loaded {len(file_transcripts)} transcripts from file: {transcript_file}")

                                # Create a simple object to mimic database transcript structure
                                class FileTranscript:
                                    def __init__(self, speaker, text):
                                        self.speaker = speaker
                                        self.text = text

                                transcripts = [FileTranscript(t['speaker'], t['text']) for t in file_transcripts]
                        except Exception as e:
                            logger.error(f"Failed to read transcript file: {e}")

        # Get interview summary
        summary = crud.get_interview_summary(db, interview_id)

        # Extract key insights and create note
        insights = []

        if summary:
            if summary.overall_assessment:
                insights.append(f"Overall: {summary.overall_assessment}")
            if summary.key_strengths:
                insights.append(f"Strengths: {', '.join(summary.key_strengths)}")
            if summary.areas_for_improvement:
                insights.append(f"Areas for improvement: {', '.join(summary.areas_for_improvement)}")
            if summary.recommendation:
                insights.append(f"Recommendation: {summary.recommendation}")

        # Count transcript exchanges (speaker can be 'interviewer' or 'recruiter')
        candidate_responses = [t for t in transcripts if t.speaker == 'candidate']
        interviewer_questions = [t for t in transcripts if t.speaker in ('interviewer', 'recruiter')]

        insights.append(f"Interview stats: {len(interviewer_questions)} questions, {len(candidate_responses)} responses")

        # Create comprehensive note
        note_text = "\n".join(insights) if insights else "Interview completed - no automated insights available"

        # Update candidate profile with interview note
        current_data = candidate.cv_parsed_data or {}
        if "interview_notes" not in current_data:
            current_data["interview_notes"] = []

        current_data["interview_notes"].append({
            "timestamp": datetime.now().isoformat(),
            "interview_id": interview_id,
            "room_name": interview.room_name,
            "note": note_text
        })

        # Update last interview date
        if "last_interview_date" not in current_data:
            current_data["last_interview_date"] = interview.actual_end.isoformat() if interview.actual_end else interview.actual_start.isoformat()

        # Mark cv_parsed_data as modified (required for SQLAlchemy to detect JSON changes)
        candidate.cv_parsed_data = current_data
        flag_modified(candidate, 'cv_parsed_data')
        db.commit()
        db.refresh(candidate)

        logger.info(f"✅ Processed interview completion for candidate {candidate.id}")

        return {
            "status": "success",
            "candidate_id": candidate.id,
            "interview_id": interview_id,
            "notes_added": len(insights),
            "message": f"Interview insights added to {candidate.name}'s profile"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to process interview completion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/evaluate-competencies")
async def evaluate_interview_competencies(
    interview_id: int,
    request: Optional[EvaluateCompetenciesRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Evaluate candidate competencies from interview conversation

    PILLAR 2.1: Competency Scoring
    Evaluates 10 competencies with 5-dimensional scoring
    """
    if not competency_evaluator:
        raise HTTPException(
            status_code=503,
            detail="Competency Evaluator not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview from database
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get conversation transcript
        transcripts = crud.get_interview_transcripts(db, interview_id)
        conversation = "\n".join([
            f"{t.speaker}: {t.text}" for t in transcripts
        ])

        if not conversation:
            raise HTTPException(
                status_code=400,
                detail="No transcript available for this interview"
            )

        logger.info(f"🎯 Evaluating competencies for interview {interview_id}")

        # Determine which competencies to evaluate
        competencies_to_eval = []
        if request and request.competencies:
            # Evaluate specific competencies
            for comp_name in request.competencies:
                try:
                    competencies_to_eval.append(CompetencyType[comp_name.upper()])
                except KeyError:
                    logger.warning(f"Unknown competency: {comp_name}")
        else:
            # Evaluate all competencies
            competencies_to_eval = list(CompetencyType)

        # Run evaluations
        results = []
        for competency in competencies_to_eval:
            logger.info(f"  Evaluating {competency.value}...")
            result = await competency_evaluator.evaluate_competency(
                competency=competency,
                conversation=conversation
            )

            # Store in database
            crud.create_competency_score(
                db=db,
                interview_id=interview_id,
                competency=competency,
                overall_score=result["overall_score"],
                depth_score=result["depth_score"],
                clarity_score=result["clarity_score"],
                relevance_score=result["relevance_score"],
                evidence_score=result["evidence_score"],
                evidence_quotes={"quotes": result["evidence_quotes"]},
                reasoning=result["reasoning"]
            )

            results.append(CompetencyScoreResponse(
                competency=result["competency"],
                overall_score=result["overall_score"],
                depth_score=result["depth_score"],
                clarity_score=result["clarity_score"],
                relevance_score=result["relevance_score"],
                evidence_score=result["evidence_score"],
                evidence_quotes=result["evidence_quotes"],
                reasoning=result["reasoning"]
            ))

        logger.info(f"✅ Evaluated {len(results)} competencies for interview {interview_id}")

        return {
            "interview_id": interview_id,
            "competencies_evaluated": len(results),
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to evaluate competencies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/analyze-star", response_model=STARAnalysisResponse)
async def analyze_star_method(
    interview_id: int,
    request: STARAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a behavioral interview answer using STAR method

    PILLAR 2.2: STAR Method Analysis
    Evaluates Situation, Task, Action, Result components
    """
    if not star_analyzer:
        raise HTTPException(
            status_code=503,
            detail="STAR Analyzer not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        logger.info(f"⭐ Analyzing STAR method for interview {interview_id}")

        # Run STAR analysis
        result = await star_analyzer.analyze(
            question=request.question,
            answer=request.answer
        )

        # Calculate STAR score
        star_score = star_analyzer.calculate_star_score(result)

        # Store in database
        crud.create_star_analysis(
            db=db,
            interview_id=interview_id,
            question=request.question,
            answer=request.answer,
            has_situation=result["has_situation"],
            has_task=result["has_task"],
            has_action=result["has_action"],
            has_result=result["has_result"],
            situation_text=result.get("situation_text"),
            task_text=result.get("task_text"),
            action_text=result.get("action_text"),
            result_text=result.get("result_text"),
            star_completion_percentage=result["star_completion_percentage"],
            result_quantified=result["result_quantified"],
            quality_rating=result["quality_rating"],
            star_score=star_score
        )

        logger.info(f"✅ STAR analysis complete: score={star_score}, quality={result['quality_rating']}")

        return STARAnalysisResponse(
            has_situation=result["has_situation"],
            has_task=result["has_task"],
            has_action=result["has_action"],
            has_result=result["has_result"],
            situation_text=result.get("situation_text"),
            task_text=result.get("task_text"),
            action_text=result.get("action_text"),
            result_text=result.get("result_text"),
            star_completion_percentage=result["star_completion_percentage"],
            quality_rating=result["quality_rating"],
            star_score=star_score
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to analyze STAR: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/detect-bluffing", response_model=BluffingDetectionResponse)
async def detect_interview_bluffing(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Detect bluffing and inconsistencies in interview conversation

    PILLAR 2.3: Bluffing & Inconsistency Detection
    Identifies suspicious patterns, vague answers, contradictions
    """
    if not bluffing_detector:
        raise HTTPException(
            status_code=503,
            detail="Bluffing Detector not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview from database
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get conversation transcript
        transcripts = crud.get_interview_transcripts(db, interview_id)
        conversation = "\n".join([
            f"{t.speaker}: {t.text}" for t in transcripts
        ])

        if not conversation:
            raise HTTPException(
                status_code=400,
                detail="No transcript available for this interview"
            )

        logger.info(f"🔍 Detecting bluffing for interview {interview_id}")

        # Run bluffing detection
        result = await bluffing_detector.detect(conversation)

        # Store red flags in database
        for flag in result.get("red_flags", []):
            crud.create_red_flag(
                db=db,
                interview_id=interview_id,
                flag_type=flag["type"],
                description=flag["explanation"],
                context=flag["quote"],  # Store the quote as context
                severity=flag["severity"]
            )

        logger.info(
            f"✅ Bluffing detection complete: score={result['bluffing_score']}, "
            f"risk={result['risk_level']}, flags={len(result.get('red_flags', []))}"
        )

        return BluffingDetectionResponse(
            bluffing_score=result["bluffing_score"],
            risk_level=result["risk_level"],
            red_flags=result.get("red_flags", []),
            credibility_assessment=result["credibility_assessment"],
            specific_concerns=result.get("specific_concerns", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to detect bluffing: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/assess-cultural-fit", response_model=CulturalFitResponse)
async def assess_cultural_fit(
    interview_id: int,
    request: Optional[CulturalFitRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Assess candidate's cultural fit with company values

    PILLAR 2.4: Cultural Fit Analysis
    Evaluates alignment across 8 cultural dimensions
    """
    if not cultural_fit_analyzer:
        raise HTTPException(
            status_code=503,
            detail="Cultural Fit Analyzer not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview from database
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get conversation transcript
        transcripts = crud.get_interview_transcripts(db, interview_id)
        conversation = "\n".join([
            f"{t.speaker}: {t.text}" for t in transcripts
        ])

        if not conversation:
            raise HTTPException(
                status_code=400,
                detail="No transcript available for this interview"
            )

        logger.info(f"🎭 Assessing cultural fit for interview {interview_id}")

        # Get custom company values if provided
        custom_values = request.company_values if request else None

        # Run cultural fit analysis
        result = await cultural_fit_analyzer.analyze(
            conversation=conversation,
            custom_values=custom_values
        )

        logger.info(
            f"✅ Cultural fit assessment complete: score={result['overall_fit_score']}, "
            f"recommendation={result['recommendation']}"
        )

        return CulturalFitResponse(
            overall_fit_score=result["overall_fit_score"],
            recommendation=result["recommendation"],
            value_alignment=result.get("value_alignment", []),
            cultural_dimensions=result.get("cultural_dimensions", {}),
            top_strengths=result.get("top_strengths", []),
            potential_concerns=result.get("potential_concerns", [])
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to assess cultural fit: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/enhanced-evaluation")
async def get_enhanced_evaluation(interview_id: int, db: Session = Depends(get_db)):
    """
    Get all enhanced evaluation results for an interview

    Returns:
    - Competency scores
    - STAR analyses
    - Bluffing detection results (red flags)
    - Cultural fit assessment (if available)
    """
    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get competency scores
        competency_scores = crud.get_interview_competency_scores(db, interview_id)

        # Get STAR analyses
        star_analyses = crud.get_interview_star_analyses(db, interview_id)

        # Get red flags (bluffing detection)
        red_flags = crud.get_interview_red_flags(db, interview_id)

        # Format response
        return {
            "interview_id": interview_id,
            "interview_status": interview.status.value,
            "competency_scores": [
                {
                    "competency": score.competency.value,
                    "overall_score": score.overall_score,
                    "depth_score": score.depth_score,
                    "clarity_score": score.clarity_score,
                    "relevance_score": score.relevance_score,
                    "evidence_score": score.evidence_score,
                    "reasoning": score.reasoning
                }
                for score in competency_scores
            ],
            "star_analyses": [
                {
                    "question": analysis.question,
                    "star_completion_percentage": analysis.star_completion_percentage,
                    "quality_rating": analysis.quality_rating,
                    "star_score": analysis.star_score,
                    "has_situation": analysis.has_situation,
                    "has_task": analysis.has_task,
                    "has_action": analysis.has_action,
                    "has_result": analysis.has_result
                }
                for analysis in star_analyses
            ],
            "bluffing_detection": {
                "red_flag_count": len(red_flags),
                "red_flags": [
                    {
                        "type": flag.flag_type,
                        "description": flag.description,
                        "quote": flag.context,  # context field contains the quote
                        "severity": flag.severity.value
                    }
                    for flag in red_flags
                ]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get enhanced evaluation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# PILLAR 1 - LIVE CO-PILOT ENDPOINTS
# ========================================

class GenerateFollowUpRequest(BaseModel):
    question: str
    answer: str
    context: Optional[Dict] = None


@app.post("/interviews/{interview_id}/generate-followup")
async def generate_followup_suggestion(
    interview_id: int,
    request: GenerateFollowUpRequest,
    db: Session = Depends(get_db)
):
    """
    Generate intelligent follow-up question suggestions

    PILLAR 1.1: Follow-Up Question Suggester
    Analyzes candidate's answer and suggests probing questions
    """
    if not followup_suggester:
        raise HTTPException(
            status_code=503,
            detail="Follow-Up Suggester not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        logger.info(f"💡 Generating follow-up suggestions for interview {interview_id}")

        # Generate suggestions
        result = await followup_suggester.generate(
            question=request.question,
            answer=request.answer,
            context=request.context
        )

        # Store top suggestion in database
        if result.get("suggestions"):
            top_suggestion = followup_suggester.get_top_suggestion(result)
            if top_suggestion:
                crud.create_follow_up_suggestion(
                    db=db,
                    interview_id=interview_id,
                    suggestion=top_suggestion["question"],
                    category=top_suggestion["category"],
                    priority=3 if top_suggestion["priority"] == "high" else 2 if top_suggestion["priority"] == "medium" else 1,
                    context=top_suggestion.get("reason")
                )

        logger.info(f"✅ Generated {len(result.get('suggestions', []))} follow-up suggestions")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate follow-up: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/pending-suggestions")
async def get_pending_suggestions(interview_id: int, db: Session = Depends(get_db)):
    """
    Get pending follow-up suggestions for an interview

    PILLAR 1.1: Returns suggestions not yet displayed to interviewer
    """
    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get pending suggestions
        suggestions = crud.get_pending_suggestions(db, interview_id)

        return {
            "interview_id": interview_id,
            "suggestion_count": len(suggestions),
            "suggestions": [
                {
                    "id": s.id,
                    "suggestion": s.suggestion,
                    "category": s.category,
                    "priority": s.priority,
                    "context": s.context,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in suggestions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get pending suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/mark-suggestion-used/{suggestion_id}")
async def mark_suggestion_used(
    interview_id: int,
    suggestion_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark a suggestion as used by the interviewer

    PILLAR 1.1: Updates displayed_to_interviewer flag
    """
    try:
        # Get suggestion
        suggestion = db.query(crud.FollowUpSuggestion).filter(
            crud.FollowUpSuggestion.id == suggestion_id,
            crud.FollowUpSuggestion.interview_id == interview_id
        ).first()

        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")

        # Mark as displayed
        suggestion.displayed_to_interviewer = True
        db.commit()

        return {
            "status": "success",
            "message": f"Suggestion {suggestion_id} marked as used"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to mark suggestion as used: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rooms/{room_name}/coverage")
async def get_interview_coverage(room_name: str):
    """
    Get real-time topic/competency coverage for an interview

    PILLAR 1.2: Coverage Tracker
    Returns coverage metrics and gaps
    """
    # Get or create coverage tracker for this room
    if room_name not in coverage_trackers:
        coverage_trackers[room_name] = CoverageTracker()

    tracker = coverage_trackers[room_name]
    coverage = tracker.get_coverage()

    return {
        "room": room_name,
        **coverage
    }


@app.post("/rooms/{room_name}/update-coverage")
async def update_interview_coverage(
    room_name: str,
    topics: Optional[List[str]] = None,
    competencies: Optional[Dict[str, float]] = None,
    question_type: Optional[str] = None,
    star_complete: Optional[bool] = None
):
    """
    Update coverage tracking for an interview

    PILLAR 1.2: Coverage Tracker
    Called by evaluation pipeline to update coverage
    """
    # Get or create coverage tracker for this room
    if room_name not in coverage_trackers:
        coverage_trackers[room_name] = CoverageTracker()

    tracker = coverage_trackers[room_name]

    # Update coverage
    coverage = tracker.update(
        topics=topics,
        competencies=competencies,
        question_type=question_type,
        star_complete=star_complete
    )

    return {
        "room": room_name,
        "status": "updated",
        **coverage
    }


@app.get("/rooms/{room_name}/quality")
async def get_interview_quality(room_name: str):
    """
    Get real-time quality score for an interview

    PILLAR 1.3: Quality Scorer
    Returns current interview quality metrics
    """
    # Get or create coverage tracker
    coverage_tracker = coverage_trackers.get(room_name)

    if not coverage_tracker or coverage_tracker.questions_asked == 0:
        # No data yet
        return {
            "room": room_name,
            "status": "no_data",
            "message": "Interview data not available yet"
        }

    # Get or create quality scorer
    if room_name not in quality_scorers:
        quality_scorers[room_name] = QualityScorer()

    quality_scorer = quality_scorers[room_name]

    # Get current coverage
    coverage = coverage_tracker.get_coverage()

    # Calculate quality score
    quality = quality_scorer.calculate(
        duration_minutes=coverage["metrics"]["duration_minutes"],
        questions_asked=coverage["metrics"]["total_questions"],
        coverage_percentage=coverage["overall_coverage"],
        star_completion_rate=coverage["metrics"]["star_completion_rate"],
        topics_covered_count=coverage["topic_count"]
    )

    return {
        "room": room_name,
        **quality
    }


# ========================================
# PILLAR 3 - AI-POWERED QUESTION BANK
# ========================================

class GenerateQuestionsRequest(BaseModel):
    competency: str
    difficulty: str = "medium"
    question_type: str = "behavioral"
    candidate_id: Optional[int] = None
    count: int = 3


@app.post("/question-bank/generate")
async def generate_questions_endpoint(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db)
):
    """
    Generate interview questions using AI

    PILLAR 3.1: Question Generator
    Creates tailored questions based on competency, difficulty, and candidate background
    """
    if not question_generator:
        raise HTTPException(
            status_code=503,
            detail="Question Generator not available - check ANTHROPIC_API_KEY"
        )

    try:
        logger.info(f"❓ Generating {request.count} questions for {request.competency} (difficulty={request.difficulty})")

        # Get candidate background if candidate_id provided
        candidate_background = None
        if request.candidate_id:
            candidate = crud.get_candidate_by_id(db, request.candidate_id)
            if candidate and candidate.cv_parsed_data:
                candidate_background = candidate.cv_parsed_data

        # Generate questions
        questions = await question_generator.generate_questions(
            competency=request.competency,
            difficulty=request.difficulty,
            question_type=request.question_type,
            candidate_background=candidate_background,
            count=request.count
        )

        # Store questions in database
        stored_questions = []
        for q in questions:
            db_question = crud.create_question_bank_entry(
                db=db,
                question_text=q["question"],
                competency=request.competency,
                difficulty=request.difficulty,
                question_type=request.question_type,
                topics=q.get("topics", []),
                follow_up_questions=q.get("follow_up_questions", []),
                evaluation_criteria=q.get("evaluation_criteria", []),
                expected_star_components=q.get("expected_star_components", []),
                generated_for_candidate_id=request.candidate_id,
                generated_by_model="claude-sonnet-4.5"
            )
            stored_questions.append({
                "id": db_question.id,
                "question": db_question.question_text,
                "topics": db_question.topics,
                "follow_up_questions": db_question.follow_up_questions,
                "evaluation_criteria": db_question.evaluation_criteria
            })

        logger.info(f"✅ Generated and stored {len(stored_questions)} questions")

        return {
            "status": "success",
            "questions": stored_questions,
            "count": len(stored_questions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/suggest-question")
async def suggest_next_question(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI-suggested next question based on coverage and performance

    PILLAR 3.2 & 3.3: Question Selector + Difficulty Calibrator
    Returns optimal next question considering coverage gaps and difficulty progression
    """
    if not question_generator:
        raise HTTPException(
            status_code=503,
            detail="Question Bank not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"

        # Get or create difficulty calibrator
        if room_name not in difficulty_calibrators:
            difficulty_calibrators[room_name] = DifficultyCalibrator()

        # Get or create question selector
        if room_name not in question_selectors:
            question_selectors[room_name] = QuestionSelector()

        calibrator = difficulty_calibrators[room_name]
        selector = question_selectors[room_name]

        # Get coverage tracker
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        # Get recommended difficulty
        target_difficulty = calibrator.get_next_difficulty()

        # Get candidate profile if available
        candidate_profile = None
        if interview.candidate and interview.candidate.cv_parsed_data:
            candidate_profile = interview.candidate.cv_parsed_data

        # Get question bank from database
        question_bank_entries = crud.get_questions_by_criteria(
            db=db,
            limit=50  # Get pool of questions to select from
        )

        # Convert to format expected by selector
        question_bank = [
            {
                "id": q.id,
                "question": q.question_text,
                "competency": q.competency,
                "difficulty": q.difficulty,
                "question_type": q.question_type,
                "topics": q.topics or [],
                "keywords": q.keywords or [],
                "follow_up_questions": q.follow_up_questions or [],
                "evaluation_criteria": q.evaluation_criteria or []
            }
            for q in question_bank_entries
        ]

        # Calculate interview duration
        interview_duration = (datetime.now() - interview.scheduled_at).total_seconds() / 60 if interview.scheduled_at else 0

        # Select best question
        selected = await selector.select_question(
            question_bank=question_bank,
            coverage=coverage["competencies"],
            target_difficulty=target_difficulty,
            candidate_profile=candidate_profile,
            interview_duration_minutes=interview_duration
        )

        if not selected:
            raise HTTPException(
                status_code=404,
                detail="No suitable questions found. Try generating more questions first."
            )

        # Store suggestion in database
        crud.create_interview_question(
            db=db,
            interview_id=interview_id,
            question_text=selected["question"],
            difficulty=selected["difficulty"],
            competency=selected["competency"],
            question_type=selected["question_type"],
            question_bank_id=selected.get("id"),
            was_ai_suggested=True,
            selection_reasoning=selected.get("selection_reasoning"),
            coverage_at_time=coverage
        )

        logger.info(f"✅ Suggested question for interview {interview_id}: {selected['question'][:50]}...")

        return {
            "interview_id": interview_id,
            "suggested_question": selected,
            "target_difficulty": target_difficulty,
            "coverage_gaps": coverage.get("gaps", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to suggest question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/questions/{question_id}/use")
async def mark_question_used_endpoint(
    interview_id: int,
    question_id: int,
    was_actually_asked: bool = True,
    was_modified: bool = False,
    db: Session = Depends(get_db)
):
    """
    Mark a suggested question as used

    PILLAR 3: Tracks question usage for analytics
    """
    try:
        # Mark question as used
        question = crud.mark_question_used(
            db=db,
            question_id=question_id,
            was_actually_asked=was_actually_asked,
            was_modified=was_modified
        )

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        logger.info(f"✅ Marked question {question_id} as used in interview {interview_id}")

        return {
            "status": "success",
            "question_id": question_id,
            "was_actually_asked": was_actually_asked,
            "was_modified": was_modified
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to mark question as used: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/questions/{question_id}/feedback")
async def update_question_feedback(
    interview_id: int,
    question_id: int,
    star_completion: Optional[float] = None,
    led_to_good_insights: Optional[bool] = None,
    interviewer_rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Update performance feedback for a question

    PILLAR 3.2: Difficulty Calibrator
    Updates calibrator with question performance data
    """
    try:
        room_name = f"interview-{interview_id}"

        # Update question performance in database
        question = crud.update_question_performance(
            db=db,
            question_id=question_id,
            star_completion=star_completion,
            led_to_good_insights=led_to_good_insights,
            interviewer_rating=interviewer_rating
        )

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update difficulty calibrator
        if room_name in difficulty_calibrators:
            calibrator = difficulty_calibrators[room_name]

            # Map response quality based on insights
            response_quality = None
            if led_to_good_insights is not None:
                response_quality = "good" if led_to_good_insights else "poor"

            calibrator.update_performance(
                question_difficulty=question.difficulty,
                star_completion=star_completion,
                response_quality=response_quality,
                interviewer_rating=interviewer_rating
            )

        logger.info(f"✅ Updated feedback for question {question_id}")

        return {
            "status": "success",
            "question_id": question_id,
            "feedback_recorded": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to update question feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/question-bank/stats")
async def get_question_bank_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about the question bank

    PILLAR 3: Analytics for question effectiveness
    """
    try:
        stats = crud.get_question_bank_stats(db)

        return {
            "status": "success",
            **stats
        }

    except Exception as e:
        logger.error(f"❌ Failed to get question bank stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# ADDITIONAL PILLAR 1 & 3 & 5 ENDPOINTS
# ========================================

@app.get("/interviews/{interview_id}/copilot/suggestions")
async def get_copilot_suggestions(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get AI Co-Pilot suggestions for the interview

    PILLAR 1: Live Co-Pilot
    Returns follow-up suggestions and coverage status
    """
    if not followup_suggester:
        raise HTTPException(
            status_code=503,
            detail="Co-Pilot not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"

        # Get coverage tracker
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        # Get pending follow-up suggestions
        pending_suggestions = crud.get_pending_suggestions(db, interview_id, limit=5)

        # Format suggestions
        follow_up_suggestions = [
            {
                "question": s.suggestion,
                "reason": s.context or "Recommended based on interview progress",
                "priority": "high" if s.priority >= 3 else "medium" if s.priority >= 2 else "low",
                "competency": s.category or "general"
            }
            for s in pending_suggestions
        ]

        # Get competency coverage status
        competency_scores = crud.get_interview_competency_scores(db, interview_id)
        covered_competencies = {score.competency.value for score in competency_scores}

        all_competencies = ["leadership", "communication", "technical_depth", "problem_solving",
                           "ownership", "adaptability", "strategic_thinking", "creativity",
                           "teamwork", "culture_fit"]

        coverage_status = []
        for comp in all_competencies:
            if comp in covered_competencies:
                score = next((s for s in competency_scores if s.competency.value == comp), None)
                coverage_status.append({
                    "competency": comp,
                    "current_score": score.overall_score if score else 0,
                    "target_score": 70,
                    "coverage_percentage": min(100, (score.overall_score / 70) * 100) if score else 0,
                    "status": "well_covered" if (score and score.overall_score >= 70) else "in_progress",
                    "suggested_questions_count": 0
                })
            else:
                coverage_status.append({
                    "competency": comp,
                    "current_score": 0,
                    "target_score": 70,
                    "coverage_percentage": 0,
                    "status": "not_started",
                    "suggested_questions_count": 2
                })

        # Calculate overall progress
        covered_count = len(covered_competencies)
        overall_progress = (covered_count / len(all_competencies)) * 100

        # Determine interview phase and recommended next step
        duration = 0
        if interview.actual_start:
            duration = (datetime.now() - interview.actual_start).total_seconds() / 60

        if duration < 10:
            interview_phase = "Opening (Building Rapport)"
            recommended_next_step = "Focus on ice-breaker questions and candidate background"
        elif duration < 30:
            interview_phase = "Core Assessment"
            recommended_next_step = "Deep dive into technical and behavioral competencies"
        elif duration < 45:
            interview_phase = "Advanced Evaluation"
            recommended_next_step = "Probe for depth and address any coverage gaps"
        else:
            interview_phase = "Closing"
            recommended_next_step = "Final clarifications and candidate questions"

        time_remaining = max(0, 60 - duration)

        return {
            "follow_up_suggestions": follow_up_suggestions,
            "coverage_status": coverage_status,
            "overall_progress": round(overall_progress, 1),
            "recommended_next_step": recommended_next_step,
            "interview_phase": interview_phase,
            "time_remaining_minutes": round(time_remaining, 1)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get co-pilot suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/copilot/coverage")
async def get_copilot_coverage(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed coverage status for the interview

    PILLAR 1: Live Co-Pilot - Coverage Tracker
    """
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        return {
            "interview_id": interview_id,
            **coverage
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get coverage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/questions/suggestions")
async def get_question_suggestions(
    interview_id: int,
    request: Dict = {},
    db: Session = Depends(get_db)
):
    """
    Get AI-suggested questions based on interview context

    PILLAR 3: Question Bank - Smart Suggestions
    """
    if not question_generator:
        raise HTTPException(
            status_code=503,
            detail="Question Generator not available - check ANTHROPIC_API_KEY"
        )

    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get coverage to determine what to focus on
        room_name = f"interview-{interview_id}"
        coverage_tracker = coverage_trackers.get(room_name, CoverageTracker())
        coverage = coverage_tracker.get_coverage()

        # Find uncovered competencies
        competency_scores = crud.get_interview_competency_scores(db, interview_id)
        covered = {score.competency.value for score in competency_scores}

        all_competencies = ["leadership", "communication", "technical_depth", "problem_solving",
                           "ownership", "adaptability", "strategic_thinking", "creativity",
                           "teamwork", "culture_fit"]

        uncovered = [c for c in all_competencies if c not in covered]
        target_competency = uncovered[0] if uncovered else all_competencies[0]

        # Generate 3-5 question suggestions
        questions = await question_generator.generate_questions(
            competency=target_competency,
            difficulty="medium",
            question_type="behavioral",
            count=3
        )

        # Format for frontend
        suggested_questions = []
        for q in questions:
            suggested_questions.append({
                "question_text": q["question"],
                "question_type": "behavioral",
                "competency": target_competency,
                "difficulty": "medium",
                "reason": f"Helps assess {target_competency} competency",
                "expected_answer_outline": "STAR format response demonstrating the competency",
                "follow_up_questions": q.get("follow_up_questions", []),
                "evaluation_criteria": q.get("evaluation_criteria", []),
                "average_response_time_seconds": 180,
                "success_rate": 0.75
            })

        return {
            "interview_id": interview_id,
            "suggested_questions": suggested_questions,
            "target_competency": target_competency,
            "coverage_gaps": uncovered
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get question suggestions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions")
async def get_all_questions(
    job_title: Optional[str] = None,
    competency: Optional[str] = None,
    difficulty: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Get questions from the question bank

    PILLAR 3: Question Bank - Browse All Questions
    """
    try:
        # Get questions from database
        questions_db = crud.get_questions_by_criteria(
            db=db,
            competency=competency,
            difficulty=difficulty,
            limit=limit
        )

        # Format for frontend
        questions = []
        for q in questions_db:
            questions.append({
                "question_text": q.question_text,
                "question_type": q.question_type or "behavioral",
                "competency": q.competency or "general",
                "difficulty": q.difficulty or "medium",
                "reason": f"From question bank (ID: {q.id})",
                "expected_answer_outline": "STAR format response",
                "follow_up_questions": q.follow_up_questions or [],
                "evaluation_criteria": q.evaluation_criteria or [],
                "average_response_time_seconds": q.average_response_time or 180,
                "success_rate": q.success_rate or 0.75
            })

        return {
            "questions": questions,
            "total": len(questions),
            "filters": {
                "job_title": job_title,
                "competency": competency,
                "difficulty": difficulty
            }
        }

    except Exception as e:
        logger.error(f"❌ Failed to get questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews")
async def list_all_interviews(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all interviews

    PILLAR 5: Interviews Management
    """
    try:
        # Get interviews from database
        interviews = crud.get_interviews(
            db=db,
            skip=(page - 1) * limit,
            limit=limit,
            status=status
        )

        # Format for frontend
        interviews_list = []
        for interview in interviews:
            # Calculate duration
            duration_minutes = interview.duration_minutes
            if not duration_minutes and interview.actual_start and interview.actual_end:
                duration_minutes = (interview.actual_end - interview.actual_start).total_seconds() / 60

            # Get summary if exists
            summaries = crud.get_interview_summaries(db, interview.id)
            overall_score = summaries[0].overall_score if summaries else None

            interviews_list.append({
                "id": interview.id,
                "candidate_name": interview.candidate.name if interview.candidate else "Unknown",
                "candidate_email": interview.candidate.email if interview.candidate else "",
                "job_title": interview.job_title or "Unknown Position",
                "scheduled_at": interview.scheduled_start.isoformat() if interview.scheduled_start else datetime.now().isoformat(),
                "started_at": interview.actual_start.isoformat() if interview.actual_start else None,
                "completed_at": interview.actual_end.isoformat() if interview.actual_end else None,
                "duration_minutes": round(duration_minutes) if duration_minutes else None,
                "status": interview.status.value,
                "overall_score": overall_score,
                "summary_generated": len(summaries) > 0
            })

        return {
            "interviews": interviews_list,
            "page": page,
            "limit": limit,
            "total": len(interviews_list)
        }

    except Exception as e:
        logger.error(f"❌ Failed to list interviews: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}")
async def get_interview_details(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about an interview

    PILLAR 5: Interview Details
    """
    try:
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get summary if exists
        summaries = crud.get_interview_summaries(db, interview_id)
        summary = None
        if summaries:
            s = summaries[0]
            summary = {
                "executive_summary": s.content,
                "key_highlights": s.highlights.get("highlights", []) if s.highlights else [],
                "strengths": s.strengths.get("strengths", []) if s.strengths else [],
                "weaknesses": s.weaknesses.get("weaknesses", []) if s.weaknesses else [],
                "hiring_recommendation": s.hiring_recommendation,
                "recommendation_confidence": s.recommendation_confidence,
                "recommendation_reasoning": s.recommendation_reasoning,
                "overall_score": s.overall_score,
                "concerns": s.weaknesses.get("concerns", []) if s.weaknesses else [],
                "standout_moments": s.highlights.get("standout_moments", []) if s.highlights else []
            }

        return {
            "id": interview.id,
            "candidate": {
                "id": interview.candidate.id if interview.candidate else None,
                "name": interview.candidate.name if interview.candidate else "Unknown",
                "email": interview.candidate.email if interview.candidate else ""
            },
            "job_title": interview.job_title,
            "scheduled_at": interview.scheduled_start.isoformat() if interview.scheduled_start else None,
            "started_at": interview.actual_start.isoformat() if interview.actual_start else None,
            "completed_at": interview.actual_end.isoformat() if interview.actual_end else None,
            "duration_minutes": interview.duration_minutes,
            "status": interview.status.value,
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get interview details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# PILLAR 4 - REAL-TIME INTERVIEWER FEEDBACK
# ========================================

class AnalyzeQuestionRequest(BaseModel):
    question: str
    context: Optional[Dict] = None


@app.post("/interviews/{interview_id}/analyze-question")
async def analyze_interviewer_question(
    interview_id: int,
    request: AnalyzeQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze interviewer question for pacing, tone, quality, and bias

    PILLAR 4: Real-Time Interviewer Feedback
    Returns comprehensive feedback on the question
    """
    if not all([tone_analyzer, quality_checker, bias_detector]):
        raise HTTPException(
            status_code=503,
            detail="Interviewer Feedback not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"

        # Extract context
        context = request.context or {}
        question_num = context.get("question_number", 1)
        duration_minutes = context.get("duration_minutes", 0.0)
        expected_type = context.get("expected_answer_type", "detailed behavioral response")
        interview_type = context.get("interview_type", "behavioral")

        logger.info(f"🔍 Analyzing question for interview {interview_id}: {request.question[:50]}...")

        # Get or create pacing monitor
        if room_name not in pacing_monitors:
            pacing_monitors[room_name] = PacingMonitor()

        pacing_monitor = pacing_monitors[room_name]

        # Run all analyses in parallel
        pacing_result, tone_result, quality_result, bias_result = await asyncio.gather(
            # Pacing is synchronous, wrap in coroutine
            asyncio.to_thread(
                pacing_monitor.track_question,
                request.question
            ),
            # AI analyses (already async)
            tone_analyzer.analyze(
                request.question,
                question_num=question_num,
                duration_minutes=duration_minutes
            ),
            quality_checker.check(
                request.question,
                interview_type=interview_type,
                expected_type=expected_type
            ),
            bias_detector.detect(request.question)
        )

        # Collect all alerts
        alerts = []

        if pacing_result.get("metrics", {}).get("is_too_fast"):
            alerts.append({
                "type": "pacing",
                "severity": "medium",
                "message": pacing_result["recommendation"]
            })

        if tone_result.get("alert"):
            alerts.append({
                "type": "tone",
                **tone_result["alert"]
            })

        if quality_result.get("alert"):
            alerts.append({
                "type": "quality",
                **quality_result["alert"]
            })

        if bias_result.get("alert"):
            alerts.append({
                "type": "bias",
                **bias_result["alert"]
            })

        # Store alerts in database if they're high severity
        for alert in alerts:
            if alert.get("severity") in ["high", "medium"]:
                # TODO: Add to database via crud function
                pass

        # Generate overall feedback
        overall_feedback = _generate_overall_feedback(
            pacing_result,
            tone_result,
            quality_result,
            bias_result
        )

        logger.info(f"✅ Analysis complete: {len(alerts)} alerts")

        return {
            "interview_id": interview_id,
            "pacing": pacing_result,
            "tone": tone_result,
            "quality": quality_result,
            "bias": bias_result,
            "overall_feedback": overall_feedback,
            "alerts": alerts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to analyze question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/feedback/current")
async def get_current_feedback(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current real-time feedback state for interview

    PILLAR 4: Returns current pacing, tone trends, quality averages
    """
    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        room_name = f"interview-{interview_id}"

        # Get summaries from each component
        pacing_summary = None
        if room_name in pacing_monitors:
            pacing_summary = pacing_monitors[room_name].get_pacing_summary()

        tone_summary = None
        if tone_analyzer:
            tone_summary = tone_analyzer.get_tone_summary()

        quality_summary = None
        if quality_checker:
            quality_summary = quality_checker.get_quality_summary()

        bias_summary = None
        if bias_detector:
            bias_summary = bias_detector.get_bias_summary()

        # Calculate duration
        duration_minutes = 0.0
        if interview.actual_start:
            duration_minutes = (datetime.now() - interview.actual_start).total_seconds() / 60

        return {
            "interview_id": interview_id,
            "duration_minutes": round(duration_minutes, 1),
            "pacing": pacing_summary,
            "tone_trends": tone_summary,
            "quality_average": quality_summary,
            "bias_status": bias_summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get current feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _generate_overall_feedback(
    pacing: Dict,
    tone: Dict,
    quality: Dict,
    bias: Dict
) -> str:
    """Generate overall feedback message from all analyses"""
    feedback_parts = []

    # Pacing feedback
    if pacing.get("status") == "ideal":
        feedback_parts.append("✅ Excellent pacing")
    elif pacing.get("status") in ["too_fast", "too_slow"]:
        feedback_parts.append(f"⚠️ {pacing.get('recommendation', '')}")

    # Tone feedback
    if tone.get("tone") == "encouraging":
        feedback_parts.append("✅ Encouraging tone")
    elif tone.get("tone") == "harsh":
        feedback_parts.append("⚠️ Consider more encouraging tone")

    # Quality feedback
    quality_rating = quality.get("quality_rating", "")
    if quality_rating in ["excellent", "good"]:
        feedback_parts.append(f"✅ {quality_rating.capitalize()} question quality")
    elif quality_rating in ["fair", "poor"]:
        feedback_parts.append(f"⚠️ Question quality could be improved")

    # Bias feedback
    if bias.get("has_bias") and bias.get("severity") in ["high", "medium"]:
        feedback_parts.append("🚨 Bias detected - use suggested alternative")
    elif not bias.get("has_bias"):
        feedback_parts.append("✅ Bias-free question")

    return " | ".join(feedback_parts) if feedback_parts else "Analysis complete"


# ========================================
# PILLAR 5 - POST-INTERVIEW ANALYSIS & REPORTING
# ========================================

class GenerateSummaryRequest(BaseModel):
    include_detailed_scores: bool = True


class GenerateReportRequest(BaseModel):
    report_type: str  # "ats", "hiring_manager", "recruiter", "full"
    include_transcript: bool = False
    format: str = "json"  # "json", "html", "markdown"


@app.post("/interviews/{interview_id}/generate-summary")
async def generate_interview_summary(
    interview_id: int,
    request: Optional[GenerateSummaryRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive interview summary

    PILLAR 5.1: Summary Generator
    Uses Claude to create executive summary, highlights, strengths/weaknesses
    """
    if not summary_generator:
        raise HTTPException(
            status_code=503,
            detail="Summary Generator not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview from database
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        logger.info(f"📝 Generating comprehensive summary for interview {interview_id}")

        # Gather all data
        candidate_data = {
            "id": interview.candidate.id,
            "name": interview.candidate.name,
            "email": interview.candidate.email
        }

        interview_data = {
            "id": interview.id,
            "job_title": interview.job_title,
            "scheduled_start": interview.scheduled_start,
            "duration_minutes": interview.duration_minutes or 0
        }

        # Get transcript
        transcripts_db = crud.get_interview_transcripts(db, interview_id)
        transcripts = [
            {
                "speaker": t.speaker.value,
                "text": t.text,
                "timestamp": t.timestamp
            }
            for t in transcripts_db
        ]

        # Get competency scores
        competency_scores_db = crud.get_interview_competency_scores(db, interview_id)
        competency_scores = [
            {
                "competency": score.competency.value,
                "overall_score": score.overall_score,
                "depth_score": score.depth_score,
                "clarity_score": score.clarity_score,
                "evidence_score": score.evidence_score,
                "reasoning": score.reasoning
            }
            for score in competency_scores_db
        ]

        # Get STAR analyses
        star_analyses_db = crud.get_interview_star_analyses(db, interview_id)
        star_analyses = [
            {
                "question": star.question,
                "star_completion_percentage": star.star_completion_percentage,
                "quality_rating": star.quality_rating,
                "has_situation": star.has_situation,
                "has_task": star.has_task,
                "has_action": star.has_action,
                "has_result": star.has_result
            }
            for star in star_analyses_db
        ]

        # Get red flags
        red_flags_db = crud.get_interview_red_flags(db, interview_id)
        red_flags = [
            {
                "flag_type": flag.flag_type,
                "description": flag.description,
                "severity": flag.severity.value
            }
            for flag in red_flags_db
        ]

        # Generate summary
        summary = await summary_generator.generate(
            interview_data=interview_data,
            candidate_data=candidate_data,
            competency_scores=competency_scores,
            star_analyses=star_analyses,
            red_flags=red_flags,
            transcripts=transcripts
        )

        # Store summary in database
        crud.create_interview_summary(
            db=db,
            interview_id=interview_id,
            summary_type="comprehensive",
            title=f"Interview Summary - {candidate_data['name']}",
            content=summary.get("executive_summary", ""),
            strengths={"strengths": summary.get("strengths", [])},
            weaknesses={"weaknesses": summary.get("weaknesses", [])},
            highlights={"highlights": summary.get("key_highlights", [])},
            next_steps={"next_steps": summary.get("next_steps", [])},
            hiring_recommendation=summary.get("hiring_recommendation"),
            recommendation_confidence=summary.get("recommendation_confidence"),
            recommendation_reasoning=summary.get("recommendation_reasoning"),
            overall_score=summary.get("metadata", {}).get("overall_score"),
            format="json"
        )

        logger.info(
            f"✅ Summary generated: {summary['hiring_recommendation']} "
            f"(score: {summary['metadata'].get('overall_score', 0):.1f})"
        )

        return {
            "interview_id": interview_id,
            "status": "success",
            "summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/interviews/{interview_id}/generate-report")
async def generate_interview_report(
    interview_id: int,
    request: GenerateReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate structured report for different audiences

    PILLAR 5.2: Report Builder
    Builds ATS, Hiring Manager, Recruiter, or Full reports
    """
    if not all([summary_generator, report_builder, export_formatter]):
        raise HTTPException(
            status_code=503,
            detail="Reporting modules not available - check ANTHROPIC_API_KEY"
        )

    try:
        # Get interview from database
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        logger.info(f"📄 Generating {request.report_type} report for interview {interview_id}")

        # Get or generate summary first
        summaries = crud.get_interview_summaries(db, interview_id)

        if summaries:
            # Use existing summary
            latest_summary = summaries[0]
            summary_data = {
                "executive_summary": latest_summary.content,
                "key_highlights": latest_summary.highlights.get("highlights", []) if latest_summary.highlights else [],
                "strengths": latest_summary.strengths.get("strengths", []) if latest_summary.strengths else [],
                "weaknesses": latest_summary.weaknesses.get("weaknesses", []) if latest_summary.weaknesses else [],
                "next_steps": latest_summary.next_steps.get("next_steps", []) if latest_summary.next_steps else [],
                "hiring_recommendation": latest_summary.hiring_recommendation,
                "recommendation_confidence": latest_summary.recommendation_confidence,
                "recommendation_reasoning": latest_summary.recommendation_reasoning,
                "metadata": {
                    "overall_score": latest_summary.overall_score
                }
            }
        else:
            # Generate new summary
            candidate_data = {
                "id": interview.candidate.id,
                "name": interview.candidate.name,
                "email": interview.candidate.email
            }

            interview_data = {
                "id": interview.id,
                "job_title": interview.job_title,
                "scheduled_start": interview.scheduled_start,
                "duration_minutes": interview.duration_minutes or 0
            }

            transcripts_db = crud.get_interview_transcripts(db, interview_id)
            transcripts = [
                {"speaker": t.speaker.value, "text": t.text, "timestamp": t.timestamp}
                for t in transcripts_db
            ]

            competency_scores_db = crud.get_interview_competency_scores(db, interview_id)
            competency_scores = [
                {
                    "competency": score.competency.value,
                    "overall_score": score.overall_score,
                    "depth_score": score.depth_score,
                    "clarity_score": score.clarity_score,
                    "evidence_score": score.evidence_score,
                    "reasoning": score.reasoning
                }
                for score in competency_scores_db
            ]

            star_analyses_db = crud.get_interview_star_analyses(db, interview_id)
            star_analyses = [
                {
                    "question": star.question,
                    "star_completion_percentage": star.star_completion_percentage,
                    "quality_rating": star.quality_rating
                }
                for star in star_analyses_db
            ]

            red_flags_db = crud.get_interview_red_flags(db, interview_id)
            red_flags = [
                {"flag_type": flag.flag_type, "description": flag.description, "severity": flag.severity.value}
                for flag in red_flags_db
            ]

            summary_data = await summary_generator.generate(
                interview_data=interview_data,
                candidate_data=candidate_data,
                competency_scores=competency_scores,
                star_analyses=star_analyses,
                red_flags=red_flags,
                transcripts=transcripts
            )

        # Prepare data for report builder
        candidate_dict = {
            "name": interview.candidate.name,
            "email": interview.candidate.email,
            "id": interview.candidate.id
        }

        interview_dict = {
            "job_title": interview.job_title,
            "scheduled_start": interview.scheduled_start,
            "duration_minutes": interview.duration_minutes or 0,
            "id": interview.id
        }

        competency_scores_db = crud.get_interview_competency_scores(db, interview_id)
        competency_scores_list = [
            {
                "competency": score.competency.value,
                "overall_score": score.overall_score,
                "depth_score": score.depth_score,
                "clarity_score": score.clarity_score,
                "evidence_score": score.evidence_score,
                "reasoning": score.reasoning
            }
            for score in competency_scores_db
        ]

        # Build report
        report = report_builder.build_report(
            report_type=request.report_type,
            summary=summary_data,
            interview_data=interview_dict,
            candidate_data=candidate_dict,
            competency_scores=competency_scores_list,
            include_transcript=request.include_transcript,
            transcripts=[]  # Can add transcripts if needed
        )

        # Export to requested format
        if request.format == "json":
            exported_content = export_formatter.export_to_json(report)
        elif request.format == "html":
            exported_content = export_formatter.export_to_html(report)
        elif request.format == "markdown":
            exported_content = export_formatter.export_to_markdown(report)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        logger.info(f"✅ Report generated: {request.report_type} ({request.format})")

        return {
            "interview_id": interview_id,
            "report_type": request.report_type,
            "format": request.format,
            "content": exported_content if request.format == "json" else None,
            "report_data": report if request.format == "json" else None,
            "html": exported_content if request.format == "html" else None,
            "markdown": exported_content if request.format == "markdown" else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to generate report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/reports")
async def list_interview_reports(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all reports for an interview

    PILLAR 5: Lists all generated reports
    """
    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get all summaries
        summaries = crud.get_interview_summaries(db, interview_id)

        return {
            "interview_id": interview_id,
            "report_count": len(summaries),
            "reports": [
                {
                    "id": summary.id,
                    "summary_type": summary.summary_type,
                    "title": summary.title,
                    "format": summary.format,
                    "generated_at": summary.generated_at.isoformat(),
                    "hiring_recommendation": summary.hiring_recommendation,
                    "overall_score": summary.overall_score
                }
                for summary in summaries
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to list reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# PILLAR 7 - RAG CONVERSATIONAL Q&A ENGINE
# ========================================

class AskQuestionRequest(BaseModel):
    question: str
    context: Optional[Dict] = None


@app.post("/interviews/{interview_id}/ask")
async def ask_interviewer_assistant(
    interview_id: int,
    request: AskQuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask the AI assistant a question during an interview

    PILLAR 7: RAG-powered conversational Q&A for real-time interviewer assistance
    """
    if not conversational_assistant:
        raise HTTPException(
            status_code=503,
            detail="RAG Q&A Engine not available - check ANTHROPIC_API_KEY and OPENAI_API_KEY"
        )

    try:
        # Get interview
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        logger.info(f"💬 Interviewer asking: {request.question[:50]}...")

        # Build interview context
        interview_context = {}

        # Add basic info
        interview_context["job_title"] = interview.job_title or "Unknown"
        interview_context["candidate_name"] = interview.candidate.name if interview.candidate else "Candidate"

        # Add duration
        if interview.actual_start:
            duration = (datetime.now() - interview.actual_start).total_seconds() / 60
            interview_context["duration_minutes"] = round(duration, 1)
        else:
            interview_context["duration_minutes"] = 0

        # Add questions asked count
        transcripts = crud.get_interview_transcripts(db, interview_id)
        interviewer_questions = [t for t in transcripts if t.speaker.value == "interviewer"]
        interview_context["questions_asked"] = len(interviewer_questions)

        # Add competencies covered
        competency_scores = crud.get_interview_competency_scores(db, interview_id)
        if competency_scores:
            interview_context["competencies_covered"] = [
                score.competency.value for score in competency_scores
            ]
        else:
            interview_context["competencies_covered"] = []

        # Add coverage gaps (simplified - could get from coverage tracker)
        all_competencies = ["leadership", "communication", "technical_depth", "problem_solving",
                           "ownership", "adaptability", "strategic_thinking", "creativity",
                           "teamwork", "culture_fit"]
        covered = set(interview_context["competencies_covered"])
        interview_context["coverage_gaps"] = [c for c in all_competencies if c not in covered]

        # Merge with provided context
        if request.context:
            interview_context.update(request.context)

        # Ask the assistant
        response = await conversational_assistant.ask(
            question=request.question,
            interview_id=interview_id,
            interview_context=interview_context
        )

        logger.info(f"✅ Answer generated with {response.get('retrieved_sources_count', 0)} sources")

        return {
            "interview_id": interview_id,
            "question": request.question,
            **response
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to answer question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/interviews/{interview_id}/assistant-history")
async def get_assistant_conversation_history(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Get conversation history with the AI assistant

    PILLAR 7: Returns all Q&A exchanges for this interview
    """
    if not conversational_assistant:
        raise HTTPException(
            status_code=503,
            detail="RAG Q&A Engine not available"
        )

    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Get conversation history
        history = conversational_assistant.get_conversation_history(interview_id)

        return {
            "interview_id": interview_id,
            "conversation_count": len(history),
            "messages": history
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/interviews/{interview_id}/assistant-history")
async def clear_assistant_conversation_history(
    interview_id: int,
    db: Session = Depends(get_db)
):
    """
    Clear conversation history with the AI assistant

    PILLAR 7: Resets the conversation context
    """
    if not conversational_assistant:
        raise HTTPException(
            status_code=503,
            detail="RAG Q&A Engine not available"
        )

    try:
        # Verify interview exists
        interview = crud.get_interview_by_id(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail=f"Interview {interview_id} not found")

        # Clear history
        conversational_assistant.clear_conversation_history(interview_id)

        return {
            "status": "success",
            "message": f"Conversation history cleared for interview {interview_id}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to clear conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge/stats")
async def get_knowledge_base_stats():
    """
    Get statistics about the knowledge base

    PILLAR 7: Returns vector store statistics
    """
    if not vector_store:
        raise HTTPException(
            status_code=503,
            detail="Vector Store not available"
        )

    try:
        info = vector_store.get_collection_info()

        return {
            "status": "available",
            "collection_name": info["name"],
            "document_count": info["count"],
            "metadata": info["metadata"]
        }

    except Exception as e:
        logger.error(f"❌ Failed to get knowledge base stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/knowledge/upload")
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = "company_doc",
    title: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Upload a document to the knowledge base

    PILLAR 7: Accepts PDF, TXT, MD files and indexes them for RAG

    Args:
        file: Uploaded file
        doc_type: Type of document (company_doc, best_practice, guide, etc.)
        title: Optional document title
        description: Optional document description
    """
    if not document_indexer or not vector_store:
        raise HTTPException(
            status_code=503,
            detail="RAG Q&A Engine not available"
        )

    try:
        logger.info(f"📤 Uploading document: {file.filename}")

        # Validate file type
        allowed_extensions = ['.txt', '.md', '.pdf']
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        # Read file content
        content_bytes = await file.read()

        # Extract text based on file type
        if file_ext == '.pdf':
            # Parse PDF file
            try:
                pdf_file = io.BytesIO(content_bytes)
                pdf_reader = PdfReader(pdf_file)

                # Extract text from all pages
                text_parts = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

                if not text_parts:
                    raise HTTPException(
                        status_code=400,
                        detail="PDF file contains no extractable text"
                    )

                content = "\n\n".join(text_parts)
                logger.info(f"📄 Extracted text from {len(pdf_reader.pages)} PDF pages")

            except Exception as e:
                logger.error(f"Failed to parse PDF: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse PDF file: {str(e)}"
                )
        else:
            # Text or markdown file
            try:
                content = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail="File must be UTF-8 encoded text"
                )

        # Create metadata
        metadata = {
            "source": "upload",
            "filename": file.filename,
            "file_type": file_ext,
            "doc_type": doc_type
        }

        if title:
            metadata["title"] = title
        if description:
            metadata["description"] = description

        # Index the document
        logger.info(f"🔍 Indexing document: {file.filename}")
        indexed_chunks = await document_indexer.index_document(
            doc_type=doc_type,
            content=content,
            metadata=metadata,
            chunk=True  # Enable chunking for long documents
        )

        # Add to vector store
        for chunk in indexed_chunks:
            await vector_store.add_document(
                doc_id=chunk["id"],
                content=chunk["content"],
                embedding=chunk["embedding"],
                metadata=chunk["metadata"]
            )

        logger.info(f"✅ Successfully indexed {len(indexed_chunks)} chunks from {file.filename}")

        return {
            "status": "success",
            "filename": file.filename,
            "chunks_indexed": len(indexed_chunks),
            "doc_type": doc_type,
            "message": f"Document '{file.filename}' successfully added to knowledge base"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting QuantCoach LiveKit API Server")
    logger.info(f"📍 Server will run on: http://0.0.0.0:8000")
    logger.info(f"📖 API Docs: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
