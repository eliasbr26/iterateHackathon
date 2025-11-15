"""
Unit tests for audio pipeline components
"""

import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, AsyncMock, patch

from audio_pipeline.models import Transcript
from audio_pipeline.audio_converter import AudioConverter


class TestTranscript:
    """Test Transcript dataclass"""

    def test_transcript_creation(self):
        """Test creating a transcript"""
        transcript = Transcript(
            text="Hello world",
            speaker="recruiter",
            start_ms=1000,
            end_ms=2000,
            is_final=True
        )

        assert transcript.text == "Hello world"
        assert transcript.speaker == "recruiter"
        assert transcript.start_ms == 1000
        assert transcript.end_ms == 2000
        assert transcript.is_final is True

    def test_transcript_defaults(self):
        """Test transcript with default values"""
        transcript = Transcript(
            text="Hello",
            speaker="candidate"
        )

        assert transcript.start_ms is None
        assert transcript.end_ms is None
        assert transcript.is_final is True

    def test_transcript_repr(self):
        """Test transcript string representation"""
        transcript = Transcript(
            text="Test message",
            speaker="recruiter",
            start_ms=1000,
            end_ms=2000,
            is_final=True
        )

        repr_str = repr(transcript)
        assert "recruiter" in repr_str
        assert "Test message" in repr_str
        assert "1000ms" in repr_str


class TestAudioConverter:
    """Test AudioConverter"""

    def test_calculate_chunk_duration(self):
        """Test chunk duration calculation"""
        # 16kHz, 16-bit, 1 second = 32000 bytes
        duration = AudioConverter.calculate_chunk_duration_ms(
            chunk_size_bytes=32000,
            sample_rate=16000,
            bit_depth=16
        )

        assert duration == 1000.0  # 1 second = 1000ms

    def test_calculate_chunk_size(self):
        """Test chunk size calculation"""
        # 100ms at 16kHz, 16-bit = 3200 bytes
        size = AudioConverter.calculate_chunk_size(
            duration_ms=100,
            sample_rate=16000,
            bit_depth=16
        )

        assert size == 3200

    def test_resample(self):
        """Test audio resampling"""
        converter = AudioConverter()

        # Create 1 second of audio at 48kHz
        audio_48k = np.random.randint(-32768, 32767, 48000, dtype=np.int16)

        # Resample to 16kHz
        resampled = converter._resample(audio_48k, 48000, 16000)

        # Should be approximately 1/3 the length
        assert len(resampled) == 16000

    def test_resample_no_op(self):
        """Test resampling with same rate (no-op)"""
        converter = AudioConverter()

        audio = np.random.randint(-32768, 32767, 16000, dtype=np.int16)
        resampled = converter._resample(audio, 16000, 16000)

        # Should be identical
        np.testing.assert_array_equal(audio, resampled)


class TestAudioPipelineIntegration:
    """Integration tests for audio pipeline"""

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self):
        """Test pipeline can be initialized"""
        from audio_pipeline import AudioPipeline

        pipeline = AudioPipeline(
            livekit_url="wss://test.com",
            livekit_room="test-room",
            livekit_token="test-token",
            elevenlabs_api_key="test-key"
        )

        assert pipeline.livekit_url == "wss://test.com"
        assert pipeline.livekit_room == "test-room"
        assert pipeline.elevenlabs_api_key == "test-key"

    @pytest.mark.asyncio
    async def test_transcript_async_iteration(self):
        """Test transcript can be yielded asynchronously"""
        async def mock_transcription():
            for i in range(3):
                yield Transcript(
                    text=f"Test {i}",
                    speaker="recruiter" if i % 2 == 0 else "candidate"
                )

        transcripts = []
        async for transcript in mock_transcription():
            transcripts.append(transcript)

        assert len(transcripts) == 3
        assert transcripts[0].speaker == "recruiter"
        assert transcripts[1].speaker == "candidate"


class TestErrorHandling:
    """Test error handling utilities"""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry succeeds on first attempt"""
        from audio_pipeline.error_handling import retry_async

        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_async(success_func, max_retries=3)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_eventually_succeeds(self):
        """Test retry succeeds after failures"""
        from audio_pipeline.error_handling import retry_async

        call_count = 0

        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = await retry_async(
            flaky_func,
            max_retries=5,
            initial_delay=0.01,
            backoff_factor=1.0
        )

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_retries(self):
        """Test retry fails after max retries"""
        from audio_pipeline.error_handling import retry_async

        async def always_fail():
            raise Exception("Always fails")

        with pytest.raises(Exception):
            await retry_async(
                always_fail,
                max_retries=2,
                initial_delay=0.01
            )


def test_imports():
    """Test all modules can be imported"""
    from audio_pipeline import AudioPipeline, Transcript
    from audio_pipeline.models import Transcript
    from audio_pipeline.audio_converter import AudioConverter
    from audio_pipeline.error_handling import retry_async

    assert AudioPipeline is not None
    assert Transcript is not None
    assert AudioConverter is not None
    assert retry_async is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
