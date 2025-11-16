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
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from room_manager import RoomManager
from agent_manager import AgentManager

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
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Event queues for SSE streaming: room_name -> asyncio.Queue
event_queues: Dict[str, List[asyncio.Queue]] = defaultdict(list)

# Session data storage: room_name -> {transcripts: [], evaluations: []}
session_data: Dict[str, dict] = defaultdict(lambda: {"transcripts": [], "evaluations": []})


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if agent_manager:
        await agent_manager.cleanup()


# Pydantic models for request/response
class CreateRoomRequest(BaseModel):
    room_name: Optional[str] = None
    max_participants: int = 10


class CreateRoomResponse(BaseModel):
    sid: str
    name: str
    max_participants: int
    creation_time: int
    interviewer_token: str
    candidate_token: str
    agent_token: str
    url: str


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


@app.get("/rooms/{room_name}/interviewer-report")
async def get_interviewer_performance_report(room_name: str):
    """
    Generate comprehensive performance report for the interviewer

    This endpoint analyzes the entire interview session and provides:
    - Overall performance score (0-10)
    - Key strengths with examples
    - Areas for improvement with actionable suggestions
    - Detailed metrics (open-ended ratio, follow-up rate, speaking balance)
    - Question quality breakdown
    - Topic coverage analysis
    - Tone consistency analysis

    Returns:
        InterviewerPerformanceReport with complete assessment
    """
    if room_name not in session_data:
        raise HTTPException(
            status_code=404,
            detail=f"No session data found for room: {room_name}"
        )

    data = session_data[room_name]
    evaluations_data = data["evaluations"]
    transcripts_data = data["transcripts"]

    if not evaluations_data:
        raise HTTPException(
            status_code=400,
            detail=f"No evaluations found for room: {room_name}. Cannot generate report."
        )

    try:
        # Import here to avoid circular dependency
        from interview_evaluator import InterviewEvaluator
        from audio_pipeline.models import EvaluationResult, Transcript
        from audio_pipeline.models import (
            SubjectRelevance, QuestionDifficulty, InterviewerTone,
            CoachingFlag, CoachingFlagType, InterviewerTechniqueAssessment,
            InterviewerTechniqueQuality
        )

        # Convert raw evaluation dicts to EvaluationResult objects
        evaluation_objects = []
        for eval_dict in evaluations_data:
            try:
                # Parse coaching flags
                coaching_flags = []
                if "coaching_flags" in eval_dict:
                    for cf_data in eval_dict["coaching_flags"]:
                        cf = CoachingFlag(
                            type=CoachingFlagType(cf_data["type"]),
                            severity=cf_data["severity"],
                            message=cf_data["message"],
                            suggestion=cf_data.get("suggestion"),
                            example_good=cf_data.get("example_good"),
                            example_bad=cf_data.get("example_bad"),
                            timestamp=datetime.fromisoformat(cf_data["timestamp"]),
                            context_quote=cf_data.get("context_quote")
                        )
                        coaching_flags.append(cf)

                # Parse interviewer technique
                interviewer_technique = None
                if "interviewer_technique" in eval_dict and eval_dict["interviewer_technique"]:
                    tech_data = eval_dict["interviewer_technique"]
                    interviewer_technique = InterviewerTechniqueAssessment(
                        open_ended_ratio=tech_data["open_ended_ratio"],
                        question_quality=InterviewerTechniqueQuality(tech_data["question_quality"]),
                        follow_up_effectiveness=InterviewerTechniqueQuality(tech_data["follow_up_effectiveness"]),
                        confidence=tech_data["confidence"]
                    )

                # Create EvaluationResult
                eval_obj = EvaluationResult(
                    timestamp=datetime.fromisoformat(eval_dict["timestamp"]),
                    window_start=datetime.fromisoformat(eval_dict["window_start"]),
                    window_end=datetime.fromisoformat(eval_dict["window_end"]),
                    transcripts_evaluated=eval_dict["transcripts_evaluated"],
                    subject_relevance=SubjectRelevance(eval_dict["subject_relevance"]),
                    question_difficulty=QuestionDifficulty(eval_dict["question_difficulty"]),
                    interviewer_tone=InterviewerTone(eval_dict["interviewer_tone"]),
                    summary=eval_dict["summary"],
                    key_topics=eval_dict["key_topics"],
                    flags=eval_dict.get("flags", []),
                    coaching_flags=coaching_flags,
                    interviewer_technique=interviewer_technique,
                    confidence_subject=eval_dict["confidence_subject"],
                    confidence_difficulty=eval_dict["confidence_difficulty"],
                    confidence_tone=eval_dict["confidence_tone"],
                    raw_llm_response=eval_dict.get("raw_llm_response")
                )
                evaluation_objects.append(eval_obj)
            except Exception as e:
                logger.warning(f"Failed to parse evaluation: {e}")
                continue

        # Convert transcript dicts to Transcript objects
        transcript_objects = []
        for t_dict in transcripts_data:
            try:
                t_obj = Transcript(
                    text=t_dict["text"],
                    speaker=t_dict["speaker"],
                    is_final=t_dict.get("is_final", True),
                    timestamp=datetime.fromisoformat(t_dict["timestamp"])
                )
                transcript_objects.append(t_obj)
            except Exception as e:
                logger.warning(f"Failed to parse transcript: {e}")
                continue

        # Get Anthropic API key
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise HTTPException(
                status_code=503,
                detail="ANTHROPIC_API_KEY not configured"
            )

        # Initialize evaluator
        evaluator = InterviewEvaluator(api_key=anthropic_api_key)

        # Generate performance report
        logger.info(f"📊 Generating interviewer performance report for room: {room_name}")
        report = await evaluator.evaluate_interviewer_performance(
            all_transcripts=transcript_objects,
            evaluation_history=evaluation_objects
        )

        return report.to_dict()

    except Exception as e:
        logger.error(f"❌ Error generating interviewer report: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate interviewer report: {str(e)}"
        )


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
