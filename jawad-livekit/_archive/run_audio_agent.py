"""
Run audio pipeline agent for room test1
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from audio_pipeline import AudioPipeline, Transcript
from room_manager import RoomManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run audio agent"""
    # Load environment variables
    load_dotenv("../.env")

    # Get configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://iterate-hackathon-1qxzyt73.livekit.cloud")
    LIVEKIT_ROOM = "test1"
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set in .env file")
        logger.info("The audio pipeline requires ElevenLabs API key for speech-to-text")
        logger.info("You can get one at: https://elevenlabs.io/")
        return

    # Generate token using room_manager
    room_manager = RoomManager()
    token = room_manager.generate_token(
        room_name=LIVEKIT_ROOM,
        participant_identity=f"audio-agent-{asyncio.get_event_loop().time()}",
        participant_name="Audio Transcription Agent",
        metadata='{"role": "agent", "type": "audio-transcription"}'
    )

    logger.info(f"🎙️  Starting audio transcription agent for room: {LIVEKIT_ROOM}")
    logger.info(f"📡 Connecting to: {LIVEKIT_URL}")

    # Create pipeline
    pipeline = AudioPipeline(
        livekit_url=LIVEKIT_URL,
        livekit_room=LIVEKIT_ROOM,
        livekit_token=token,
        elevenlabs_api_key=ELEVENLABS_API_KEY,
        language="en",
        recruiter_identity="interviewer",
        candidate_identity="candidate"
    )

    print("\n" + "="*60)
    print("🎙️  REAL-TIME AUDIO TRANSCRIPTION")
    print("="*60 + "\n")

    try:
        # Start transcription and process transcripts
        async for transcript in pipeline.start_transcription():
            # Format output
            marker = "✓" if transcript.is_final else "~"
            speaker_emoji = "👔" if transcript.speaker == "recruiter" else "👤"

            # Display transcript
            if transcript.is_final:
                print(f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}")
            else:
                # For partial transcripts, show in real-time
                print(
                    f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}",
                    end='\r'
                )

    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Error in pipeline: {e}", exc_info=True)
    finally:
        logger.info("🛑 Stopping pipeline...")
        await pipeline.stop()
        logger.info("✅ Pipeline stopped")


if __name__ == "__main__":
    asyncio.run(main())
