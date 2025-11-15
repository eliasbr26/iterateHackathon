"""
Audio format conversion utilities
Converts LiveKit/WebRTC audio frames to PCM format for ElevenLabs
"""

import logging
import numpy as np
from typing import Optional
from livekit import rtc

logger = logging.getLogger(__name__)


class AudioConverter:
    """
    Converts audio frames from LiveKit/WebRTC format to PCM format
    suitable for ElevenLabs STT (16kHz, mono, 16-bit PCM)
    """

    # Target format for ElevenLabs
    TARGET_SAMPLE_RATE = 16000  # 16 kHz
    TARGET_CHANNELS = 1  # Mono
    TARGET_BIT_DEPTH = 16  # 16-bit

    def __init__(self):
        """Initialize audio converter"""
        self._resampler_cache = {}

    def convert_frame(
        self,
        frame: rtc.AudioFrame,
        target_sample_rate: int = TARGET_SAMPLE_RATE
    ) -> bytes:
        """
        Convert LiveKit AudioFrame to PCM bytes

        Args:
            frame: LiveKit AudioFrame
            target_sample_rate: Target sample rate (default: 16000 Hz)

        Returns:
            PCM audio data as bytes (16-bit, mono)
        """
        try:
            # Get frame properties
            sample_rate = frame.sample_rate
            num_channels = frame.num_channels
            samples_per_channel = frame.samples_per_channel

            # Extract audio data as numpy array
            # LiveKit provides audio as planar float32 format
            audio_data = np.frombuffer(
                frame.data,
                dtype=np.int16
            ).reshape(num_channels, samples_per_channel)

            # Convert to mono if needed
            if num_channels > 1:
                # Average all channels to create mono
                audio_mono = audio_data.mean(axis=0).astype(np.int16)
            else:
                audio_mono = audio_data[0]

            # Resample if needed
            if sample_rate != target_sample_rate:
                audio_mono = self._resample(
                    audio_mono,
                    sample_rate,
                    target_sample_rate
                )

            # Convert to 16-bit PCM bytes
            pcm_bytes = audio_mono.astype(np.int16).tobytes()

            return pcm_bytes

        except Exception as e:
            logger.error(f"Error converting audio frame: {e}")
            raise

    def _resample(
        self,
        audio: np.ndarray,
        orig_sr: int,
        target_sr: int
    ) -> np.ndarray:
        """
        Resample audio to target sample rate using linear interpolation

        Args:
            audio: Audio data as numpy array
            orig_sr: Original sample rate
            target_sr: Target sample rate

        Returns:
            Resampled audio as numpy array
        """
        if orig_sr == target_sr:
            return audio

        # Calculate duration and number of target samples
        duration = len(audio) / orig_sr
        target_length = int(duration * target_sr)

        # Use numpy's linear interpolation for resampling
        # This is a simple but effective method for speech
        indices = np.linspace(0, len(audio) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio)), audio)

        return resampled.astype(np.int16)

    def buffer_to_pcm(
        self,
        buffer: bytes,
        sample_rate: int,
        channels: int,
        bit_depth: int = 16
    ) -> bytes:
        """
        Convert raw audio buffer to target PCM format

        Args:
            buffer: Raw audio buffer
            sample_rate: Source sample rate
            channels: Number of channels
            bit_depth: Bit depth (8, 16, 24, or 32)

        Returns:
            Converted PCM data as bytes
        """
        try:
            # Determine dtype based on bit depth
            if bit_depth == 16:
                dtype = np.int16
            elif bit_depth == 32:
                dtype = np.int32
            elif bit_depth == 8:
                dtype = np.uint8
            else:
                raise ValueError(f"Unsupported bit depth: {bit_depth}")

            # Convert buffer to numpy array
            audio = np.frombuffer(buffer, dtype=dtype)

            # Reshape if multi-channel
            if channels > 1:
                audio = audio.reshape(-1, channels)
                # Convert to mono by averaging channels
                audio = audio.mean(axis=1).astype(dtype)

            # Resample if needed
            if sample_rate != self.TARGET_SAMPLE_RATE:
                audio = self._resample(audio, sample_rate, self.TARGET_SAMPLE_RATE)

            # Ensure 16-bit output
            if dtype != np.int16:
                # Normalize and convert to int16
                if dtype == np.int32:
                    audio = (audio / 65536).astype(np.int16)
                elif dtype == np.uint8:
                    audio = ((audio - 128) * 256).astype(np.int16)

            return audio.tobytes()

        except Exception as e:
            logger.error(f"Error converting buffer to PCM: {e}")
            raise

    @staticmethod
    def calculate_chunk_duration_ms(
        chunk_size_bytes: int,
        sample_rate: int = TARGET_SAMPLE_RATE,
        bit_depth: int = TARGET_BIT_DEPTH
    ) -> float:
        """
        Calculate duration of audio chunk in milliseconds

        Args:
            chunk_size_bytes: Size of chunk in bytes
            sample_rate: Sample rate in Hz
            bit_depth: Bit depth (bits per sample)

        Returns:
            Duration in milliseconds
        """
        bytes_per_sample = bit_depth // 8
        num_samples = chunk_size_bytes / bytes_per_sample
        duration_sec = num_samples / sample_rate
        return duration_sec * 1000

    @staticmethod
    def calculate_chunk_size(
        duration_ms: float,
        sample_rate: int = TARGET_SAMPLE_RATE,
        bit_depth: int = TARGET_BIT_DEPTH
    ) -> int:
        """
        Calculate chunk size in bytes for a given duration

        Args:
            duration_ms: Duration in milliseconds
            sample_rate: Sample rate in Hz
            bit_depth: Bit depth (bits per sample)

        Returns:
            Chunk size in bytes
        """
        duration_sec = duration_ms / 1000
        num_samples = int(duration_sec * sample_rate)
        bytes_per_sample = bit_depth // 8
        return num_samples * bytes_per_sample
