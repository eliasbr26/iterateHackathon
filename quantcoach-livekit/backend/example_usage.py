"""
Example usage of the QuantCoach LiveKit Backend

This script demonstrates:
1. Creating a LiveKit room
2. Generating access tokens for participants
3. Using the audio pipeline for real-time transcription
"""

import asyncio
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from room_manager import RoomManager
from audio_pipeline import AudioPipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_create_room():
    """
    Example 1: Create a room and generate tokens for all participants
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 1: Create Room and Generate Tokens")
    logger.info("=" * 60)

    try:
        # Initialize RoomManager
        manager = RoomManager()

        # Create a unique room name
        room_name = f"interview-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"Creating room: {room_name}")

        # Create the room
        room = await manager.create_room(room_name, max_participants=10)
        logger.info(f"✅ Room created successfully!")
        logger.info(f"   Room SID: {room['sid']}")
        logger.info(f"   Room Name: {room['name']}")

        # Generate tokens for different participant types
        logger.info("\n📝 Generating access tokens...")

        # Interviewer token
        interviewer_token = manager.generate_token(
            room_name=room_name,
            participant_identity=f"interviewer-{datetime.now().timestamp()}",
            participant_name="John Interviewer",
            metadata='{"role": "interviewer"}',
        )
        logger.info(f"✅ Interviewer token: {interviewer_token[:50]}...")

        # Candidate token
        candidate_token = manager.generate_token(
            room_name=room_name,
            participant_identity=f"candidate-{datetime.now().timestamp()}",
            participant_name="Jane Candidate",
            metadata='{"role": "candidate"}',
        )
        logger.info(f"✅ Candidate token: {candidate_token[:50]}...")

        # Agent token (for transcription bot)
        agent_token = manager.generate_token(
            room_name=room_name,
            participant_identity=f"agent-{datetime.now().timestamp()}",
            participant_name="Transcription Agent",
            metadata='{"role": "agent", "type": "transcription"}',
        )
        logger.info(f"✅ Agent token: {agent_token[:50]}...")

        # List all rooms
        logger.info("\n📋 Listing all active rooms...")
        rooms = await manager.list_rooms()
        for r in rooms:
            logger.info(f"   - {r['name']} ({r['num_participants']} participants)")

        # Cleanup
        await manager.close()
        logger.info("\n✅ Example 1 completed successfully!\n")

        return room_name, agent_token

    except Exception as e:
        logger.error(f"❌ Error in example 1: {e}")
        raise


async def example_audio_pipeline(room_name: str, agent_token: str):
    """
    Example 2: Use the audio pipeline for real-time transcription

    NOTE: This requires actual participants to join the room and speak.
    In production, you would have users connect via the frontend.
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 2: Audio Pipeline Transcription")
    logger.info("=" * 60)

    # Check if ElevenLabs API key is configured
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_api_key:
        logger.warning("⚠️  ELEVENLABS_API_KEY not configured - skipping audio pipeline example")
        logger.info("   To use audio transcription, add your ElevenLabs API key to .env")
        return

    try:
        # Initialize audio pipeline
        livekit_url = os.getenv("LIVEKIT_URL")

        logger.info(f"🎤 Setting up audio pipeline for room: {room_name}")
        logger.info("⏳ Waiting for participants to join...")
        logger.info("   (Users should connect via the frontend with their tokens)")

        pipeline = AudioPipeline(
            livekit_url=livekit_url,
            livekit_room=room_name,
            livekit_token=agent_token,
            elevenlabs_api_key=elevenlabs_api_key,
            language="en",
            recruiter_identity="interviewer",
            candidate_identity="candidate"
        )

        # Start transcription (will wait for participants)
        logger.info("🎧 Starting real-time transcription...")
        logger.info("   Speak into your microphone to see transcripts appear below:")
        logger.info("-" * 60)

        transcript_count = 0
        max_transcripts = 50  # Limit for example

        async for transcript in pipeline.start_transcription():
            # Display transcript
            logger.info(f"[{transcript.speaker.upper()}] {transcript.text}")

            transcript_count += 1
            if transcript_count >= max_transcripts:
                logger.info(f"\n📊 Reached {max_transcripts} transcripts, stopping...")
                break

        # Cleanup
        await pipeline.stop()
        logger.info("\n✅ Example 2 completed successfully!\n")

    except Exception as e:
        logger.error(f"❌ Error in example 2: {e}")
        if "ElevenLabs" in str(e):
            logger.info("💡 Make sure your ELEVENLABS_API_KEY is valid and has credits")
        raise


async def example_list_participants():
    """
    Example 3: List participants in a room
    """
    logger.info("=" * 60)
    logger.info("EXAMPLE 3: List Room Participants")
    logger.info("=" * 60)

    try:
        manager = RoomManager()

        # List all rooms
        rooms = await manager.list_rooms()

        if not rooms:
            logger.info("📋 No active rooms found")
            return

        # Get participants for each room
        for room in rooms:
            room_name = room['name']
            logger.info(f"\n🏠 Room: {room_name}")

            participants = await manager.get_room_participants(room_name)

            if participants:
                logger.info(f"   👥 Participants ({len(participants)}):")
                for p in participants:
                    logger.info(f"      - {p['name']} ({p['identity']}) - {p['state']}")
            else:
                logger.info("   👥 No participants")

        await manager.close()
        logger.info("\n✅ Example 3 completed successfully!\n")

    except Exception as e:
        logger.error(f"❌ Error in example 3: {e}")
        raise


async def main():
    """
    Run all examples
    """
    logger.info("\n" + "=" * 60)
    logger.info("🚀 QuantCoach LiveKit Backend - Example Usage")
    logger.info("=" * 60 + "\n")

    try:
        # Example 1: Create room and generate tokens
        room_name, agent_token = await example_create_room()

        # Wait a bit
        await asyncio.sleep(2)

        # Example 3: List participants (room should be empty at this point)
        await example_list_participants()

        # Example 2: Audio pipeline (requires users to join)
        # Uncomment the line below to test audio transcription
        # await example_audio_pipeline(room_name, agent_token)

        logger.info("=" * 60)
        logger.info("✅ All examples completed!")
        logger.info("=" * 60)
        logger.info("\n💡 Next steps:")
        logger.info("   1. Start the FastAPI server: python server.py")
        logger.info("   2. Connect via the frontend to test video/audio")
        logger.info("   3. Use the /rooms/create endpoint to create rooms")
        logger.info("   4. Use tokens to join rooms from the frontend\n")

    except Exception as e:
        logger.error(f"❌ Error running examples: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
