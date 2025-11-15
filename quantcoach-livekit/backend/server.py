"""
FastAPI Server for QuantCoach LiveKit Interview Platform

Provides REST API endpoints for:
- Creating interview rooms
- Generating access tokens
- Managing participants
- Health checks

Compatible with the QuantCoach frontend VideoArea component.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from room_manager import RoomManager

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
        await room_manager.delete_room(room_name)
        logger.info(f"✅ Room deleted: {room_name}")
        return {"status": "success", "message": f"Room {room_name} deleted"}
    except Exception as e:
        logger.error(f"❌ Failed to delete room: {e}")
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
