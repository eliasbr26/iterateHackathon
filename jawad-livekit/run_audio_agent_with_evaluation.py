"""
Run audio pipeline agent with real-time LLM evaluation

Integrates:
- Audio transcription (ElevenLabs STT)
- Transcript storage (JSON + TXT)
- Real-time LLM evaluation (Anthropic Claude)
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
from transcript_buffer import TranscriptBuffer
from interview_evaluator import InterviewEvaluator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class TranscriptAndEvaluationStorage:
    """Handles saving transcripts AND evaluations to files"""

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
        self.evaluations_file = self.session_dir / "evaluations.json"
        self.evaluations_text_file = self.session_dir / "evaluations.txt"

        self.transcripts = []
        self.evaluations = []

        logger.info(f"💾 Saving session data to: {self.session_dir}")

    def add_transcript(self, transcript: Transcript):
        """Add a transcript to storage"""
        if not transcript.is_final:
            return

        transcript_data = {
            "timestamp": datetime.now().isoformat(),
            "speaker": transcript.speaker,
            "text": transcript.text,
            "is_final": transcript.is_final
        }

        self.transcripts.append(transcript_data)
        self._save_transcripts_json()
        self._save_transcript_text(transcript_data)

    def add_evaluation(self, evaluation):
        """Add an evaluation result to storage"""
        self.evaluations.append(evaluation.to_dict())
        self._save_evaluations_json()
        self._save_evaluation_text(evaluation)

    def _save_transcripts_json(self):
        """Save all transcripts to JSON file"""
        with open(self.json_file, 'w') as f:
            json.dump({
                "room": self.room_name,
                "session_start": self.transcripts[0]["timestamp"] if self.transcripts else None,
                "transcripts": self.transcripts
            }, f, indent=2)

    def _save_transcript_text(self, transcript_data: dict):
        """Append transcript to human-readable text file"""
        with open(self.text_file, 'a') as f:
            speaker_emoji = "👔" if transcript_data["speaker"] == "recruiter" else "👤"
            timestamp = datetime.fromisoformat(transcript_data["timestamp"]).strftime("%H:%M:%S")
            f.write(f"[{timestamp}] {speaker_emoji} {transcript_data['speaker'].upper()}: {transcript_data['text']}\n")

    def _save_evaluations_json(self):
        """Save all evaluations to JSON file"""
        with open(self.evaluations_file, 'w') as f:
            json.dump({
                "room": self.room_name,
                "total_evaluations": len(self.evaluations),
                "evaluations": self.evaluations
            }, f, indent=2)

    def _save_evaluation_text(self, evaluation):
        """Append evaluation to human-readable text file"""
        with open(self.evaluations_text_file, 'a') as f:
            timestamp = evaluation.timestamp.strftime("%H:%M:%S")
            f.write(f"\n{'='*80}\n")
            f.write(f"[{timestamp}] EVALUATION\n")
            f.write(f"{'='*80}\n")
            f.write(f"Window: {evaluation.window_start.strftime('%H:%M:%S')} - {evaluation.window_end.strftime('%H:%M:%S')}\n")
            f.write(f"Transcripts: {evaluation.transcripts_evaluated}\n")
            f.write(f"\n")
            f.write(f"📊 Subject Relevance: {evaluation.subject_relevance.value.upper()} (confidence: {evaluation.confidence_subject:.2f})\n")
            f.write(f"🎯 Question Difficulty: {evaluation.question_difficulty.value.upper()} (confidence: {evaluation.confidence_difficulty:.2f})\n")
            f.write(f"💬 Interviewer Tone: {evaluation.interviewer_tone.value.upper()} (confidence: {evaluation.confidence_tone:.2f})\n")
            f.write(f"\n")
            f.write(f"📝 Summary: {evaluation.summary}\n")
            f.write(f"\n")
            f.write(f"🔑 Key Topics: {', '.join(evaluation.key_topics) if evaluation.key_topics else 'None'}\n")
            if evaluation.flags:
                f.write(f"\n")
                f.write(f"🚩 Flags:\n")
                for flag in evaluation.flags:
                    f.write(f"   - {flag}\n")
            f.write(f"\n")

    def get_summary(self) -> dict:
        """Get session summary"""
        return {
            "total_transcripts": len(self.transcripts),
            "total_evaluations": len(self.evaluations),
            "speakers": list(set(t["speaker"] for t in self.transcripts)),
            "output_dir": str(self.session_dir)
        }


async def main():
    """Main function to run audio agent with evaluation"""
    # Load environment variables
    load_dotenv("../.env")

    # Get configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL", "wss://iterate-hackathon-1qxzyt73.livekit.cloud")
    LIVEKIT_ROOM = "test1"
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set in .env file")
        return

    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        logger.error("Please add: ANTHROPIC_API_KEY=your-api-key to ../.env")
        return

    # Initialize components
    storage = TranscriptAndEvaluationStorage(room_name=LIVEKIT_ROOM)
    buffer = TranscriptBuffer(
        window_size_seconds=20.0,
        overlap_seconds=10.0,
        min_transcripts_for_evaluation=2
    )
    evaluator = InterviewEvaluator(api_key=ANTHROPIC_API_KEY)

    # Generate token using room_manager
    room_manager = RoomManager()
    token = room_manager.generate_token(
        room_name=LIVEKIT_ROOM,
        participant_identity=f"audio-agent-{asyncio.get_event_loop().time()}",
        participant_name="Audio Transcription + Evaluation Agent",
        metadata='{"role": "agent", "type": "audio-evaluation"}'
    )

    logger.info(f"🎙️  Starting audio transcription + evaluation agent for room: {LIVEKIT_ROOM}")
    logger.info(f"📡 Connecting to: {LIVEKIT_URL}")
    logger.info(f"🤖 LLM Evaluation: ENABLED (20s windows with 10s overlap)")

    # Create pipeline (using ElevenLabs Scribe v2 Realtime)
    pipeline = AudioPipeline(
        livekit_url=LIVEKIT_URL,
        livekit_room=LIVEKIT_ROOM,
        livekit_token=token,
        stt_api_key=ELEVENLABS_API_KEY,
        language="en",
        recruiter_identity="interviewer",
        candidate_identity="candidate",
        stt_provider="elevenlabs"
    )

    print("\n" + "="*80)
    print("🎙️  REAL-TIME AUDIO TRANSCRIPTION + LLM EVALUATION")
    print("="*80 + "\n")

    # Queue for evaluation tasks
    evaluation_queue = asyncio.Queue()

    async def evaluation_worker():
        """Background worker for LLM evaluations"""
        while True:
            try:
                window = await evaluation_queue.get()
                if window is None:  # Sentinel to stop
                    break

                logger.info(f"🤖 Starting LLM evaluation for window...")
                evaluation = await evaluator.evaluate(window)
                storage.add_evaluation(evaluation)

                # Display evaluation
                print(f"\n{'─'*80}")
                print(f"🤖 EVALUATION [{evaluation.timestamp.strftime('%H:%M:%S')}]")
                print(f"{'─'*80}")
                print(f"📊 Subject: {evaluation.subject_relevance.value.upper()} (conf: {evaluation.confidence_subject:.2f})")
                print(f"🎯 Difficulty: {evaluation.question_difficulty.value.upper()} (conf: {evaluation.confidence_difficulty:.2f})")
                print(f"💬 Tone: {evaluation.interviewer_tone.value.upper()} (conf: {evaluation.confidence_tone:.2f})")
                print(f"📝 {evaluation.summary}")
                if evaluation.key_topics:
                    print(f"🔑 Topics: {', '.join(evaluation.key_topics)}")
                if evaluation.flags:
                    print(f"🚩 Flags: {', '.join(evaluation.flags)}")
                print(f"{'─'*80}\n")

                evaluation_queue.task_done()

            except Exception as e:
                logger.error(f"Error in evaluation worker: {e}", exc_info=True)

    # Start evaluation worker
    eval_task = asyncio.create_task(evaluation_worker())

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

                # Add to buffer and check for evaluation trigger
                window = buffer.add_transcript(transcript)
                if window:
                    logger.info(f"📦 Window ready for evaluation ({len(window)} transcripts)")
                    await evaluation_queue.put(window)

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

        # Flush remaining buffer
        final_window = buffer.flush()
        if final_window:
            logger.info("Evaluating final window...")
            await evaluation_queue.put(final_window)

        # Stop evaluation worker
        await evaluation_queue.put(None)
        await eval_task

        await pipeline.stop()

        # Show summary
        summary = storage.get_summary()
        logger.info(f"✅ Pipeline stopped")
        logger.info(f"📊 Session summary:")
        logger.info(f"   - Total transcripts: {summary['total_transcripts']}")
        logger.info(f"   - Total evaluations: {summary['total_evaluations']}")
        logger.info(f"   - Speakers: {', '.join(summary['speakers'])}")
        logger.info(f"   - Saved to: {summary['output_dir']}")


if __name__ == "__main__":
    asyncio.run(main())
