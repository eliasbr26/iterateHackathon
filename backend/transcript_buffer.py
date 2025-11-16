"""
Transcript buffering system for windowed LLM evaluation

Implements sliding window with overlap and speaker turn detection
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from audio_pipeline.models import Transcript, BufferedWindow

logger = logging.getLogger(__name__)


class TranscriptBuffer:
    """
    Manages transcript buffering with sliding windows

    Features:
    - 20-second evaluation window
    - 10-second overlap between windows
    - Speaker turn detection
    - Hybrid triggering (time-based OR speaker turn)
    """

    def __init__(
        self,
        window_size_seconds: float = 20.0,
        overlap_seconds: float = 10.0,
        min_transcripts_for_evaluation: int = 2
    ):
        """
        Initialize transcript buffer

        Args:
            window_size_seconds: Maximum window duration before triggering evaluation
            overlap_seconds: How much context to preserve between windows
            min_transcripts_for_evaluation: Minimum transcripts needed to trigger
        """
        self.window_size_seconds = window_size_seconds
        self.overlap_seconds = overlap_seconds
        self.min_transcripts_for_evaluation = min_transcripts_for_evaluation

        self.buffer: List[Transcript] = []
        self.window_start_time: Optional[datetime] = None
        self.last_speaker: Optional[str] = None

        logger.info(
            f"TranscriptBuffer initialized: "
            f"window={window_size_seconds}s, overlap={overlap_seconds}s"
        )

    def add_transcript(self, transcript: Transcript) -> Optional[BufferedWindow]:
        """
        Add a transcript to buffer and check if window should be evaluated

        Args:
            transcript: Final transcript to add (must have is_final=True)

        Returns:
            BufferedWindow if evaluation should be triggered, None otherwise
        """
        if not transcript.is_final:
            logger.warning("Attempted to add non-final transcript to buffer - ignoring")
            return None

        # Add timestamp if not present
        if transcript.timestamp is None:
            transcript.timestamp = datetime.now()

        # Initialize window start time on first transcript
        if self.window_start_time is None:
            self.window_start_time = transcript.timestamp
            logger.debug("Window start initialized")

        # Add to buffer
        self.buffer.append(transcript)

        # Check for speaker turn change
        speaker_changed = (
            self.last_speaker is not None and
            self.last_speaker != transcript.speaker
        )
        self.last_speaker = transcript.speaker

        # Calculate window duration
        window_duration = (transcript.timestamp - self.window_start_time).total_seconds()

        # Determine if we should trigger evaluation
        should_evaluate = False
        trigger_reason = None

        # Check minimum buffer size first
        if len(self.buffer) < self.min_transcripts_for_evaluation:
            return None

        # Trigger condition 1: Time-based (window exceeded)
        if window_duration >= self.window_size_seconds:
            should_evaluate = True
            trigger_reason = "time_limit"
            logger.debug(
                f"Triggering evaluation: time limit reached ({window_duration:.1f}s)"
            )

        # Trigger condition 2: Speaker turn (hybrid mode)
        elif speaker_changed and window_duration >= 5.0:
            # Only trigger on speaker turn if we have at least 5s of content
            should_evaluate = True
            trigger_reason = "speaker_turn"
            logger.debug(
                f"Triggering evaluation: speaker turn after {window_duration:.1f}s"
            )

        if should_evaluate:
            return self._create_window(trigger_reason)

        return None

    def _create_window(self, trigger_reason: str) -> BufferedWindow:
        """
        Create a BufferedWindow from current buffer and prepare for next window

        Args:
            trigger_reason: Why evaluation was triggered ("time_limit" or "speaker_turn")

        Returns:
            BufferedWindow ready for evaluation
        """
        if not self.buffer:
            raise ValueError("Cannot create window from empty buffer")

        # Count speaker turns
        speaker_turns = 0
        prev_speaker = None
        for t in self.buffer:
            if prev_speaker is not None and prev_speaker != t.speaker:
                speaker_turns += 1
            prev_speaker = t.speaker

        # Create window
        window = BufferedWindow(
            transcripts=self.buffer.copy(),
            window_start=self.window_start_time,
            window_end=self.buffer[-1].timestamp,
            speaker_turns=speaker_turns
        )

        logger.info(
            f"Created window: {len(window)} transcripts, "
            f"{window.duration_seconds():.1f}s, "
            f"{speaker_turns} turns, "
            f"trigger={trigger_reason}"
        )

        # Prepare buffer for next window with overlap
        self._prepare_next_window()

        return window

    def _prepare_next_window(self) -> None:
        """
        Keep overlap transcripts and reset window start time
        """
        if not self.buffer:
            return

        # Calculate cutoff time for overlap
        last_timestamp = self.buffer[-1].timestamp
        overlap_cutoff = last_timestamp - timedelta(seconds=self.overlap_seconds)

        # Keep transcripts within overlap period
        overlap_buffer = [
            t for t in self.buffer
            if t.timestamp >= overlap_cutoff
        ]

        logger.debug(
            f"Keeping {len(overlap_buffer)}/{len(self.buffer)} transcripts for overlap"
        )

        self.buffer = overlap_buffer

        # Reset window start to beginning of overlap
        if self.buffer:
            self.window_start_time = self.buffer[0].timestamp
        else:
            self.window_start_time = None

    def flush(self) -> Optional[BufferedWindow]:
        """
        Force evaluation of remaining buffer contents

        Returns:
            BufferedWindow if buffer has content, None otherwise
        """
        if len(self.buffer) < self.min_transcripts_for_evaluation:
            logger.debug("Flush called but insufficient transcripts in buffer")
            return None

        logger.info("Flushing buffer")
        return self._create_window("flush")

    def get_buffer_info(self) -> dict:
        """Get current buffer state for debugging"""
        if not self.buffer:
            return {
                "buffer_size": 0,
                "window_duration_seconds": 0,
                "speakers": []
            }

        window_duration = (
            self.buffer[-1].timestamp - self.window_start_time
        ).total_seconds()

        speakers = list(set(t.speaker for t in self.buffer))

        return {
            "buffer_size": len(self.buffer),
            "window_duration_seconds": window_duration,
            "speakers": speakers,
            "window_start": self.window_start_time.isoformat() if self.window_start_time else None,
            "last_speaker": self.last_speaker
        }
