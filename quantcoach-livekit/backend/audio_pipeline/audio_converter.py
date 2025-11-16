"""
Audio format conversion utilities for LiveKit to ElevenLabs
"""

import numpy as np
import logging
from livekit import rtc

logger = logging.getLogger(__name__)


class AudioConverter:
    """
    Converts LiveKit audio frames to PCM format for ElevenLabs STT

    LiveKit provides: 48kHz sample rate
    ElevenLabs expects: 16kHz, mono, 16-bit PCM
    """

    TARGET_SAMPLE_RATE = 16000  # Hz
    SOURCE_SAMPLE_RATE = 48000  # Hz (LiveKit default)
    BYTES_PER_SAMPLE = 2  # 16-bit = 2 bytes

    def __init__(self):
        self.downsample_ratio = self.SOURCE_SAMPLE_RATE // self.TARGET_SAMPLE_RATE
        logger.debug(f"AudioConverter initialized (downsample ratio: {self.downsample_ratio})")

    def convert_frame(self, frame: rtc.AudioFrame) -> bytes:
        """
        Convert LiveKit AudioFrame to 16kHz PCM bytes

        Args:
            frame: LiveKit AudioFrame (48kHz)

        Returns:
            PCM audio bytes (16kHz, mono, 16-bit)
        """
        try:
            # Get raw audio data from frame
            # LiveKit frames are already in PCM format
            data = frame.data

            # Convert bytes to numpy array (int16)
            audio_array = np.frombuffer(data, dtype=np.int16)

            # Downsample from 48kHz to 16kHz (take every 3rd sample)
            downsampled = audio_array[::self.downsample_ratio]

            # Convert back to bytes
            return downsampled.tobytes()

        except Exception as e:
            logger.error(f"Error converting audio frame: {e}")
            raise

    def calculate_chunk_size(self, duration_ms: int) -> int:
        """
        Calculate target chunk size in bytes for a given duration

        Args:
            duration_ms: Desired duration in milliseconds

        Returns:
            Number of bytes for that duration at 16kHz
        """
        samples = (self.TARGET_SAMPLE_RATE * duration_ms) // 1000
        return samples * self.BYTES_PER_SAMPLE
