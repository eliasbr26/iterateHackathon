"""
Advanced example with transcript storage and real-time analysis
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
from dotenv import load_dotenv

from audio_pipeline import AudioPipeline, Transcript
from audio_pipeline.logging_config import setup_colored_logging

# Setup colored logging
setup_colored_logging(level="INFO")
logger = logging.getLogger(__name__)


class TranscriptAnalyzer:
    """Analyzes transcripts in real-time"""

    def __init__(self):
        self.word_counts = defaultdict(int)
        self.speaker_stats = defaultdict(lambda: {"words": 0, "messages": 0})

    def analyze(self, transcript: Transcript) -> Dict:
        """Analyze a transcript and return statistics"""
        if not transcript.is_final:
            return {}

        # Count words
        words = transcript.text.split()
        word_count = len(words)

        # Update stats
        self.speaker_stats[transcript.speaker]["words"] += word_count
        self.speaker_stats[transcript.speaker]["messages"] += 1

        # Count word frequency
        for word in words:
            word_lower = word.lower().strip('.,!?;:')
            if len(word_lower) > 3:  # Only count words > 3 chars
                self.word_counts[word_lower] += 1

        return {
            "word_count": word_count,
            "total_words": self.speaker_stats[transcript.speaker]["words"],
            "total_messages": self.speaker_stats[transcript.speaker]["messages"]
        }

    def get_top_words(self, n: int = 10) -> List[tuple]:
        """Get top N most frequent words"""
        return sorted(self.word_counts.items(), key=lambda x: x[1], reverse=True)[:n]

    def get_summary(self) -> Dict:
        """Get overall summary"""
        return {
            "speaker_stats": dict(self.speaker_stats),
            "total_unique_words": len(self.word_counts),
            "top_words": self.get_top_words(10)
        }


class TranscriptStorage:
    """Stores transcripts to file"""

    def __init__(self, output_dir: str = "transcripts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Create session file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = os.path.join(output_dir, f"session_{timestamp}.json")
        self.transcripts: List[Dict] = []

    def save(self, transcript: Transcript) -> None:
        """Save transcript to storage"""
        if not transcript.is_final:
            return

        # Convert to dict
        transcript_dict = {
            "timestamp": datetime.now().isoformat(),
            "speaker": transcript.speaker,
            "text": transcript.text,
            "start_ms": transcript.start_ms,
            "end_ms": transcript.end_ms
        }

        self.transcripts.append(transcript_dict)

        # Write to file
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.transcripts, f, indent=2, ensure_ascii=False)

    def get_full_transcript(self) -> str:
        """Get full transcript as formatted text"""
        lines = []
        for t in self.transcripts:
            timestamp = datetime.fromisoformat(t["timestamp"]).strftime("%H:%M:%S")
            speaker = t["speaker"].upper()
            text = t["text"]
            lines.append(f"[{timestamp}] {speaker}: {text}")
        return "\n".join(lines)

    def export_summary(self, analyzer: TranscriptAnalyzer) -> str:
        """Export session summary"""
        summary_file = self.session_file.replace('.json', '_summary.txt')

        summary = analyzer.get_summary()
        speaker_stats = summary["speaker_stats"]

        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("INTERVIEW TRANSCRIPT SUMMARY\n")
            f.write("=" * 60 + "\n\n")

            f.write(f"Session: {os.path.basename(self.session_file)}\n")
            f.write(f"Total messages: {len(self.transcripts)}\n\n")

            f.write("Speaker Statistics:\n")
            f.write("-" * 60 + "\n")
            for speaker, stats in speaker_stats.items():
                f.write(f"\n{speaker.upper()}:\n")
                f.write(f"  Messages: {stats['messages']}\n")
                f.write(f"  Total words: {stats['words']}\n")
                f.write(f"  Avg words/message: {stats['words'] / stats['messages']:.1f}\n")

            f.write("\n\n")
            f.write("Top 10 Most Frequent Words:\n")
            f.write("-" * 60 + "\n")
            for word, count in summary["top_words"]:
                f.write(f"  {word}: {count}\n")

            f.write("\n\n")
            f.write("Full Transcript:\n")
            f.write("=" * 60 + "\n\n")
            f.write(self.get_full_transcript())

        logger.info(f"Summary exported to {summary_file}")
        return summary_file


async def main():
    """Main function with advanced features"""
    # Load environment variables
    load_dotenv()

    # Get configuration
    LIVEKIT_URL = os.getenv("LIVEKIT_URL")
    LIVEKIT_ROOM = os.getenv("LIVEKIT_ROOM")
    LIVEKIT_TOKEN = os.getenv("LIVEKIT_TOKEN")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    if not all([LIVEKIT_URL, LIVEKIT_ROOM, LIVEKIT_TOKEN, ELEVENLABS_API_KEY]):
        logger.error("Missing required environment variables")
        logger.error("Please check your .env file")
        return

    # Initialize components
    storage = TranscriptStorage()
    analyzer = TranscriptAnalyzer()

    # Create pipeline
    pipeline = AudioPipeline(
        livekit_url=LIVEKIT_URL,
        livekit_room=LIVEKIT_ROOM,
        livekit_token=LIVEKIT_TOKEN,
        elevenlabs_api_key=ELEVENLABS_API_KEY,
        language="en"
    )

    logger.info("=" * 60)
    logger.info("ADVANCED REAL-TIME TRANSCRIPTION")
    logger.info("=" * 60)
    logger.info(f"Room: {LIVEKIT_ROOM}")
    logger.info(f"Output: {storage.session_file}")
    logger.info("Press Ctrl+C to stop and export summary")
    logger.info("=" * 60)
    print()

    try:
        # Start transcription
        transcript_count = 0

        async for transcript in pipeline.start_transcription():
            # Display transcript
            marker = "✓" if transcript.is_final else "~"
            speaker_emoji = "👔" if transcript.speaker == "recruiter" else "👤"

            if transcript.is_final:
                # Analyze
                stats = analyzer.analyze(transcript)

                # Store
                storage.save(transcript)

                # Display with stats
                print(f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}")

                if stats:
                    print(f"   └─ Words: {stats['word_count']} | "
                          f"Total: {stats['total_words']} words in {stats['total_messages']} messages")

                transcript_count += 1

                # Show progress every 10 transcripts
                if transcript_count % 10 == 0:
                    summary = analyzer.get_summary()
                    print(f"\n📊 Progress: {transcript_count} transcripts | "
                          f"{summary['total_unique_words']} unique words\n")

            else:
                # Show partial transcript (updating)
                print(f"{speaker_emoji} [{transcript.speaker.upper()}] {marker} {transcript.text}",
                      end='\r', flush=True)

    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
    except Exception as e:
        logger.error(f"Error in pipeline: {e}", exc_info=True)
    finally:
        logger.info("Stopping pipeline...")
        await pipeline.stop()

        # Export summary
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING SUMMARY")
        logger.info("=" * 60)

        summary_file = storage.export_summary(analyzer)
        summary = analyzer.get_summary()

        print("\n📊 Final Statistics:")
        print("-" * 60)
        for speaker, stats in summary["speaker_stats"].items():
            print(f"\n{speaker.upper()}:")
            print(f"  Messages: {stats['messages']}")
            print(f"  Words: {stats['words']}")
            print(f"  Avg: {stats['words'] / stats['messages']:.1f} words/message")

        print("\n\n🔤 Top 10 Words:")
        print("-" * 60)
        for word, count in summary["top_words"]:
            print(f"  {word}: {count}")

        print("\n" + "=" * 60)
        print(f"✅ Session saved to: {storage.session_file}")
        print(f"✅ Summary saved to: {summary_file}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
