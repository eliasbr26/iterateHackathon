"""
Run audio pipeline agent with transcript storage

This version saves transcripts to:
1. JSON file (for processing/analysis)
2. Text file (human-readable)
3. Optional: Could also save to database
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from pathlib import Path
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


class TranscriptStorage:
    """Handles saving transcripts to files"""

    def __init__(self, room_name: str, output_dir: str = "transcripts"):
        self.room_name = room_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Create timestamped session folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"{room_name}_{timestamp}"
        self.session_dir.mkdir(exist_ok=True)

        # File paths
        self.json_file = self.session_dir / "transcripts.json"
        self.text_file = self.session_dir / "transcripts.txt"

        self.transcripts = []

        logger.info(f"💾 Saving transcripts to: {self.session_dir}")

    def add_transcript(self, transcript: Transcript):
        """Add a transcript to storage"""
        # Only save final transcripts (not partial ones)
        if not transcript.is_final:
            return

        transcript_data = {
            "timestamp": datetime.now().isoformat(),
            "speaker": transcript.speaker,
            "text": transcript.text,
            "is_final": transcript.is_final
        }

        self.transcripts.append(transcript_data)

        # Save incrementally (so data isn't lost if session crashes)
        self._save_json()
        self._save_text(transcript_data)

    def _save_json(self):
        """Save all transcripts to JSON file"""
        with open(self.json_file, 'w') as f:
            json.dump({
                "room": self.room_name,
                "session_start": self.transcripts[0]["timestamp"] if self.transcripts else None,
                "transcripts": self.transcripts
            }, f, indent=2)

    def _save_text(self, transcript_data: dict):
        """Append transcript to human-readable text file"""
        with open(self.text_file, 'a') as f:
            speaker_emoji = "👔" if transcript_data["speaker"] == "recruiter" else "👤"
            timestamp = datetime.fromisoformat(transcript_data["timestamp"]).strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {speaker_emoji} {transcript_data['speaker'].upper()}: {transcript_data['text']}\n")

    def get_summary(self) -> dict:
        """Get session summary"""
        return {
            "total_transcripts": len(self.transcripts),
            "speakers": list(set(t["speaker"] for t in self.transcripts)),
            "output_dir": str(self.session_dir)
        }


async def main():
    """Main function to run audio agent with storage"""
    # Load environment variables
    load_dotenv("../.env")

    # Get configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://iterate-hackathon-1qxzyt73.livekit.cloud")
    LIVEKIT_ROOM = "test1"
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set in .env file")
        return

    # Initialize transcript storage
    storage = TranscriptStorage(room_name=LIVEKIT_ROOM)

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
    print("🎙️  REAL-TIME AUDIO TRANSCRIPTION (WITH STORAGE)")
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
                # Save final transcript
                storage.add_transcript(transcript)
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

        # Show summary
        summary = storage.get_summary()
        logger.info(f"✅ Pipeline stopped")
        logger.info(f"📊 Session summary:")
        logger.info(f"   - Total transcripts: {summary['total_transcripts']}")
        logger.info(f"   - Speakers: {', '.join(summary['speakers'])}")
        logger.info(f"   - Saved to: {summary['output_dir']}")


if __name__ == "__main__":
    asyncio.run(main())
