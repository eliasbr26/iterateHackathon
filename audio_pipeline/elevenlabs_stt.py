"""
ElevenLabs Batch STT - Clean implementation using REST API
Sends PCM audio buffers to ElevenLabs and returns transcribed text
"""

import logging
import aiohttp
from io import BytesIO
from typing import Optional
import struct

logger = logging.getLogger(__name__)


class ElevenLabsSTT:
    """
    ElevenLabs Batch Speech-to-Text client

    Simple REST API client that sends audio chunks and returns transcripts.
    No WebSockets, no streaming, no complexity - just clean batch processing.
    """

    API_URL = "https://api.elevenlabs.io/v1/speech-to-text"

    def __init__(
        self,
        api_key: str,
        language: str = "en",
        model_id: str = "eleven_multilingual_stt"
    ):
        """
        Initialize ElevenLabs batch STT client

        Args:
            api_key: ElevenLabs API key
            language: Language code (e.g., "en", "fr", "es")
            model_id: ElevenLabs model (default: "eleven_multilingual_stt")
        """
        self.api_key = api_key
        self.language = language
        self.model_id = model_id
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session for connection pooling"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def transcribe_pcm(
        self,
        audio_pcm: bytes,
        sample_rate: int = 16000,
        speaker: str = "unknown"
    ) -> str:
        """
        Transcribe PCM audio using ElevenLabs batch STT

        Args:
            audio_pcm: Raw PCM audio bytes (16-bit mono)
            sample_rate: Sample rate in Hz (default: 16000)
            speaker: Speaker label for debug logging

        Returns:
            Transcribed text as string (empty if no speech detected)
        """
        if len(audio_pcm) == 0:
            logger.debug(f"[{speaker}] Empty audio chunk, skipping transcription")
            return ""

        try:
            session = await self._get_session()

            # Convert PCM to WAV format (ElevenLabs expects WAV)
            wav_buffer = self._pcm_to_wav(audio_pcm, sample_rate)
            wav_bytes = wav_buffer.getvalue()

            # Debug log
            logger.debug(f"[{speaker}] Sending WAV to ElevenLabs: {len(wav_bytes)} bytes")

            # Prepare multipart form data with file field
            data = aiohttp.FormData()
            data.add_field(
                'file',
                wav_bytes,
                filename='audio.wav',
                content_type='audio/wav'
            )
            data.add_field('model_id', self.model_id)

            # Only add language if it's set
            if self.language:
                data.add_field('language', self.language)

            # Prepare headers
            headers = {'xi-api-key': self.api_key}

            # Send request
            async with session.post(
                self.API_URL,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    text = result.get('text', '').strip()

                    if text:
                        logger.info(f"[{speaker}] Transcribed: {text}")
                    else:
                        logger.debug(f"[{speaker}] No speech detected in audio chunk")

                    return text

                else:
                    error_text = await response.text()
                    logger.error(
                        f"[{speaker}] ElevenLabs API error: {response.status} {error_text}"
                    )
                    return ""

        except aiohttp.ClientError as e:
            logger.error(f"[{speaker}] Network error: {e}")
            return ""
        except Exception as e:
            logger.error(f"[{speaker}] Transcription error: {e}")
            return ""

    def _pcm_to_wav(self, pcm_data: bytes, sample_rate: int) -> BytesIO:
        """
        Convert raw PCM bytes to WAV format

        Args:
            pcm_data: Raw PCM audio (16-bit mono)
            sample_rate: Sample rate in Hz

        Returns:
            BytesIO buffer containing WAV file
        """
        num_channels = 1
        sample_width = 2  # 16-bit = 2 bytes

        wav_buffer = BytesIO()

        # RIFF header
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', 36 + len(pcm_data)))
        wav_buffer.write(b'WAVE')

        # fmt chunk
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<I', 16))  # Chunk size
        wav_buffer.write(struct.pack('<H', 1))   # PCM format
        wav_buffer.write(struct.pack('<H', num_channels))
        wav_buffer.write(struct.pack('<I', sample_rate))
        wav_buffer.write(struct.pack('<I', sample_rate * num_channels * sample_width))
        wav_buffer.write(struct.pack('<H', num_channels * sample_width))
        wav_buffer.write(struct.pack('<H', sample_width * 8))

        # data chunk
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', len(pcm_data)))
        wav_buffer.write(pcm_data)

        wav_buffer.seek(0)
        return wav_buffer

    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("HTTP session closed")
