"""
Simple LiveKit Agent - Connects to a room without AI services

This agent joins a LiveKit room as a participant and can be seen in the dashboard.
No API keys required.
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from livekit import rtc

# Load environment variables
load_dotenv("../.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleAgent:
    """Basic agent that joins a room"""

    def __init__(self, room_name: str):
        self.room_name = room_name
        self.room = rtc.Room()
        self.url = os.getenv("LIVEKIT_URL")
        self.api_key = os.getenv("LIVEKIT_API_KEY")
        self.api_secret = os.getenv("LIVEKIT_API_SECRET")

        if not all([self.url, self.api_key, self.api_secret]):
            raise ValueError("Missing LiveKit credentials in .env")

    def generate_token(self) -> str:
        """Generate access token for the agent"""
        from livekit import api
        from datetime import timedelta

        token = (
            api.AccessToken(self.api_key, self.api_secret)
            .with_identity(f"agent-simple-{asyncio.get_event_loop().time()}")
            .with_name("Simple Agent")
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=self.room_name,
                    can_publish=False,  # Agent won't publish audio/video
                    can_subscribe=True,
                )
            )
            .with_ttl(timedelta(hours=2))
            .with_metadata('{"role": "agent", "type": "observer"}')
        )
        return token.to_jwt()

    async def connect(self):
        """Connect to the LiveKit room"""

        # Set up event handlers
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"✅ Participant connected: {participant.identity} ({participant.name})")

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"❌ Participant disconnected: {participant.identity}")

        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.TrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            track_type = "audio" if track.kind == rtc.TrackKind.KIND_AUDIO else "video"
            logger.info(f"🎵 Track subscribed: {track_type} from {participant.identity}")

        @self.room.on("track_published")
        def on_track_published(
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant,
        ):
            track_type = "audio" if publication.kind == rtc.TrackKind.KIND_AUDIO else "video"
            logger.info(f"📢 Track published: {track_type} by {participant.identity}")

        @self.room.on("disconnected")
        def on_disconnected():
            logger.info("🔌 Agent disconnected from room")

        # Generate token and connect
        token = self.generate_token()
        logger.info(f"🤖 Connecting agent to room: {self.room_name}")

        try:
            await self.room.connect(self.url, token)
            logger.info(f"✅ Agent successfully connected to room: {self.room_name}")
            room_sid = await self.room.sid()
            logger.info(f"📊 Room SID: {room_sid}")
            logger.info(f"👥 Current participants: {len(self.room.remote_participants)}")

            # List current participants
            for identity, participant in self.room.remote_participants.items():
                logger.info(f"   - {participant.name} ({identity})")

            # Keep the agent running
            logger.info("🎧 Agent is now listening to the room...")
            logger.info("Press Ctrl+C to disconnect")

            # Run indefinitely until interrupted
            while True:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("\n⚠️  Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Error connecting to room: {e}")
            raise
        finally:
            await self.disconnect()

    async def disconnect(self):
        """Disconnect from the room"""
        if self.room:
            logger.info("👋 Disconnecting agent...")
            await self.room.disconnect()
            logger.info("✅ Agent disconnected")


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python simple_agent.py <room_name>")
        print("Example: python simple_agent.py test1")
        sys.exit(1)

    room_name = sys.argv[1]
    agent = SimpleAgent(room_name)
    await agent.connect()


if __name__ == "__main__":
    asyncio.run(main())
