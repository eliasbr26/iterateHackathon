"""
LiveKit Room Manager

Utilities for creating rooms and generating access tokens for participants.
"""

import os
from datetime import timedelta
from typing import Optional

from dotenv import load_dotenv
from livekit import api

load_dotenv()


class RoomManager:
    """Manages LiveKit rooms and access tokens"""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.url = url or os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        self.api_key = api_key or os.getenv("LIVEKIT_API_KEY")
        self.api_secret = api_secret or os.getenv("LIVEKIT_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError(
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set in environment"
            )

        # LiveKit API instance will be created lazily
        self.lkapi = None

    def _ensure_api(self):
        """Lazily create LiveKit API instance if needed"""
        if self.lkapi is None:
            self.lkapi = api.LiveKitAPI(
                url=self.url,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
        return self.lkapi

    async def create_room(self, room_name: str, max_participants: int = 10) -> dict:
        """
        Create a new LiveKit room for an interview session

        Args:
            room_name: Unique name for the room (e.g., "interview-2024-11-15-001")
            max_participants: Maximum number of participants allowed

        Returns:
            Room information dictionary
        """
        try:
            lkapi = self._ensure_api()
            room = await lkapi.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    max_participants=max_participants,
                    empty_timeout=600,  # Room closes 10 minutes after last participant leaves
                )
            )
            return {
                "sid": room.sid,
                "name": room.name,
                "max_participants": room.max_participants,
                "creation_time": room.creation_time,
            }
        except Exception as e:
            raise Exception(f"Failed to create room: {e}")

    def generate_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> str:
        """
        Generate an access token for a participant to join a room

        Args:
            room_name: Name of the room to join
            participant_identity: Unique identifier for the participant
            participant_name: Display name for the participant
            metadata: Optional metadata (JSON string)

        Returns:
            JWT access token
        """
        token = (
            api.AccessToken(self.api_key, self.api_secret)
            .with_identity(participant_identity)
            .with_name(participant_name or participant_identity)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .with_ttl(timedelta(hours=2))
        )

        if metadata:
            token.with_metadata(metadata)

        return token.to_jwt()

    async def list_rooms(self) -> list:
        """List all active rooms"""
        try:
            lkapi = self._ensure_api()
            rooms = await lkapi.room.list_rooms(api.ListRoomsRequest())
            return [
                {
                    "sid": room.sid,
                    "name": room.name,
                    "num_participants": room.num_participants,
                    "creation_time": room.creation_time,
                }
                for room in rooms.rooms
            ]
        except Exception as e:
            raise Exception(f"Failed to list rooms: {e}")

    async def get_room_participants(self, room_name: str) -> list:
        """Get list of participants in a room"""
        try:
            lkapi = self._ensure_api()
            participants = await lkapi.room.list_participants(
                api.ListParticipantsRequest(room=room_name)
            )
            return [
                {
                    "sid": p.sid,
                    "identity": p.identity,
                    "name": p.name,
                    "state": str(p.state),
                }
                for p in participants.participants
            ]
        except Exception as e:
            raise Exception(f"Failed to get participants: {e}")

    async def delete_room(self, room_name: str):
        """Delete a room"""
        try:
            lkapi = self._ensure_api()
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=room_name))
        except Exception as e:
            raise Exception(f"Failed to delete room: {e}")

    async def close(self):
        """Close the API session"""
        await self.lkapi.aclose()


# Example usage
async def example_usage():
    """Example of how to use the RoomManager"""
    manager = RoomManager()

    try:
        # Create a room
        room = await manager.create_room("interview-session-001")
        print(f"Created room: {room}")

        # Generate tokens for participants
        interviewer_token = manager.generate_token(
            room_name="interview-session-001",
            participant_identity="interviewer-1",
            participant_name="John Interviewer",
            metadata='{"role": "interviewer"}',
        )
        print(f"Interviewer token: {interviewer_token[:50]}...")

        candidate_token = manager.generate_token(
            room_name="interview-session-001",
            participant_identity="candidate-1",
            participant_name="Jane Candidate",
            metadata='{"role": "candidate"}',
        )
        print(f"Candidate token: {candidate_token[:50]}...")

        agent_token = manager.generate_token(
            room_name="interview-session-001",
            participant_identity="analysis-agent",
            participant_name="Interview Analyzer",
            metadata='{"role": "agent", "type": "analyzer"}',
        )
        print(f"Agent token: {agent_token[:50]}...")

        # List all rooms
        rooms = await manager.list_rooms()
        print(f"Active rooms: {rooms}")

    finally:
        await manager.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(example_usage())
