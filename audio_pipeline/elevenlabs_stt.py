"""
ElevenLabs Realtime STT WebSocket connection handler
"""

import asyncio
import json
import logging
import base64
import urllib.parse
from typing import Optional, AsyncIterator
from dataclasses import dataclass
from websockets.asyncio.client import connect

logger = logging.getLogger(__name__)


@dataclass
class TranscriptChunk:
    """Raw transcript chunk from ElevenLabs"""
    text: str
    is_final: bool
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None


class ElevenLabsSTT:
    """
    ElevenLabs Realtime Speech-to-Text WebSocket client

    Handles streaming audio to ElevenLabs and receiving transcripts in real-time
    """

    # ElevenLabs Realtime STT WebSocket endpoint
    WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"

    def __init__(
        self,
        api_key: str,
        speaker_label: str,
        language: str = "en",
        model_id: str = "scribe_v2_realtime"
    ):
        """
        Initialize ElevenLabs STT client

        Args:
            api_key: ElevenLabs API key
            speaker_label: Label for this speaker ("recruiter" or "candidate")
            language: Language code (default: "en")
            model_id: ElevenLabs model ID (default: "scribe_v2_realtime")
        """
        self.api_key = api_key
        self.speaker_label = speaker_label
        self.language = language
        self.model_id = model_id

        self.ws = None
        self._connected = False
        self._session_id: Optional[str] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to ElevenLabs"""
        if self._connected:
            logger.warning(f"[{self.speaker_label}] Already connected to ElevenLabs")
            return

        try:
            # Build query parameters for Realtime STT
            params = {
                "model_id": self.model_id,
                "audio_format": "pcm_16000",
                "language_code": self.language,
                "commit_strategy": "vad",
                "include_timestamps": False,
            }

            # Build full URI with query parameters
            uri = f"{self.WS_URL}?{urllib.parse.urlencode(params)}"

            # API key in headers
            headers = {
                "xi-api-key": self.api_key
            }

            logger.info(f"[{self.speaker_label}] Connecting to ElevenLabs STT WebSocket...")
            logger.debug(f"[{self.speaker_label}] URI: {uri}")

            self.ws = await connect(
                uri,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self._connected = True
            logger.info(f"[{self.speaker_label}] Connected to ElevenLabs STT")

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Failed to connect to ElevenLabs: {e}")
            raise

    async def send_audio_chunk(self, audio_data: bytes) -> None:
        """
        Send audio chunk to ElevenLabs

        Args:
            audio_data: PCM audio data (16kHz, mono, 16-bit)
        """
        if not self._connected or not self.ws:
            raise ConnectionError("Not connected to ElevenLabs")

        try:
            # Base64-encode the PCM audio bytes
            audio_b64 = base64.b64encode(audio_data).decode("ascii")

            # Build message in Realtime STT format
            message = {
                "message_type": "input_audio_chunk",
                "audio_base_64": audio_b64,
                "sample_rate": 16000,
            }

            await self.ws.send(json.dumps(message))

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error sending audio chunk: {e}")
            raise

    async def receive_transcripts(self) -> AsyncIterator[TranscriptChunk]:
        """
        Receive transcript chunks from ElevenLabs

        Yields:
            TranscriptChunk objects as they arrive
        """
        if not self._connected or not self.ws:
            raise ConnectionError("Not connected to ElevenLabs")

        logger.info(f"[{self.speaker_label}] Starting to receive transcripts...")

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    message_type = data.get("message_type")

                    if message_type == "session_started":
                        # Session initialization
                        self._session_id = data.get("session_id")
                        logger.info(
                            f"[{self.speaker_label}] Session started: {self._session_id}"
                        )

                    elif message_type == "partial_transcript":
                        # Partial (non-final) transcript
                        text = data.get("text", "").strip()

                        if text:
                            chunk = TranscriptChunk(
                                text=text,
                                is_final=False,
                                start_ms=None,
                                end_ms=None
                            )

                            logger.debug(
                                f"[{self.speaker_label}] [PARTIAL] {text}"
                            )

                            yield chunk

                    elif message_type in ("committed_transcript", "committed_transcript_with_timestamps"):
                        # Final transcript
                        text = data.get("text", "").strip()

                        if text:
                            chunk = TranscriptChunk(
                                text=text,
                                is_final=True,
                                start_ms=None,
                                end_ms=None
                            )

                            logger.info(
                                f"[{self.speaker_label}] [FINAL] {text}"
                            )

                            yield chunk

                    elif message_type in ("auth_error", "quota_exceeded", "input_error", "error"):
                        # Error messages
                        error_msg = data.get("message", data.get("error", "Unknown error"))
                        logger.error(
                            f"[{self.speaker_label}] ElevenLabs error ({message_type}): {error_msg}"
                        )
                        logger.debug(f"[{self.speaker_label}] Full error data: {data}")

                except json.JSONDecodeError:
                    logger.warning(f"[{self.speaker_label}] Failed to decode message")
                except Exception as e:
                    logger.error(f"[{self.speaker_label}] Error processing message: {e}")

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error receiving transcripts: {e}")
            raise
        finally:
            self._connected = False
            logger.info(f"[{self.speaker_label}] Stopped receiving transcripts")

    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self.ws and self._connected:
            try:
                await self.ws.close()
                logger.info(f"[{self.speaker_label}] Disconnected from ElevenLabs")
            except Exception as e:
                logger.error(f"[{self.speaker_label}] Error disconnecting: {e}")
            finally:
                self._connected = False
                self.ws = None

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._connected

    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID"""
        return self._session_id
