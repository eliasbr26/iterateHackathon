"""
Example usage of the audio pipeline
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

from audio_pipeline import AudioPipeline, Transcript

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating pipeline usage"""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://your-livekit-server.com")
    LIVEKIT_ROOM = os.getenv("LIVEKIT_ROOM", "interview-room")
    LIVEKIT_TOKEN = os.getenv("LIVEKIT_TOKEN")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    if not LIVEKIT_TOKEN:
        raise ValueError("LIVEKIT_TOKEN not set in environment")
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in environment")

    # Create pipeline
    pipeline = AudioPipeline(
        livekit_url=LIVEKIT_URL,
        livekit_room=LIVEKIT_ROOM,
        livekit_token=LIVEKIT_TOKEN,
        elevenlabs_api_key=ELEVENLABS_API_KEY,
        language="en",  # Use "fr" for French
        recruiter_identity="interviewer",
        candidate_identity="candidate"
    )

    logger.info("Starting audio pipeline...")
    logger.info(f"Room: {LIVEKIT_ROOM}")
    logger.info("Waiting for transcripts...")
    print("\n" + "="*60)
    print("REAL-TIME TRANSCRIPTION")
    print("="*60 + "\n")

    try:
        # Start transcription and process transcripts
        async for transcript in pipeline.start_transcription():
            # Format output based on whether it's final or partial
            marker = "✓" if transcript.is_final else "~"
            speaker_emoji = "👔" if transcript.speaker == "recruiter" else "👤"

            # Display transcript
            if transcript.is_final:
                print(f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}")
            else:
                # For partial transcripts, show in real-time without newline
                print(
                    f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}",
                    end='\r'
                )

            # Optional: You can also store transcripts in a database,
            # send to another service, or perform real-time analysis here

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error in pipeline: {e}", exc_info=True)
    finally:
        logger.info("Stopping pipeline...")
        await pipeline.stop()
        logger.info("Pipeline stopped")


if __name__ == "__main__":
    asyncio.run(main())
