"""
Deepgram Realtime STT WebSocket connection handler
"""

import asyncio
import json
import logging
from typing import Optional, AsyncIterator
from dataclasses import dataclass
from websockets.asyncio.client import connect

logger = logging.getLogger(__name__)


@dataclass
class TranscriptChunk:
    """Raw transcript chunk from Deepgram"""
    text: str
    is_final: bool
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None


class DeepgramSTT:
    """
    Deepgram Realtime Speech-to-Text WebSocket client

    Handles streaming audio to Deepgram and receiving transcripts in real-time
    Uses Nova-2 model for best accuracy with technical content
    """

    # Deepgram WebSocket endpoint
    WS_URL = "wss://api.deepgram.com/v1/listen"

    def __init__(
        self,
        api_key: str,
        speaker_label: str,
        language: str = "en",
        model: str = "nova-2"
    ):
        """
        Initialize Deepgram STT client

        Args:
            api_key: Deepgram API key
            speaker_label: Label for this speaker ("recruiter" or "candidate")
            language: Language code (default: "en")
            model: Deepgram model (default: "nova-2" for best accuracy)
        """
        self.api_key = api_key
        self.speaker_label = speaker_label
        self.language = language
        self.model = model

        self.ws = None
        self._connected = False
        self._request_id: Optional[str] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to Deepgram"""
        if self._connected:
            logger.warning(f"[{self.speaker_label}] Already connected to Deepgram")
            return

        try:
            # Build query parameters for Deepgram streaming
            params = {
                "model": self.model,
                "language": self.language,
                "encoding": "linear16",  # PCM 16-bit
                "sample_rate": "16000",
                "channels": "1",  # Mono
                "punctuate": "true",
                "interim_results": "true",  # Get partial transcripts
                "vad_events": "true",  # Voice activity detection
                "endpointing": "300",  # 300ms silence = end of utterance
                "smart_format": "true",  # Better formatting
            }

            # Build full URI
            params_str = "&".join([f"{k}={v}" for k, v in params.items()])
            uri = f"{self.WS_URL}?{params_str}"

            # API key in headers
            headers = {
                "Authorization": f"Token {self.api_key}"
            }

            logger.info(f"[{self.speaker_label}] Connecting to Deepgram STT WebSocket...")

            self.ws = await connect(
                uri,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10
            )

            self._connected = True
            logger.info(f"[{self.speaker_label}] Connected to Deepgram STT")

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Failed to connect to Deepgram: {e}")
            raise

    async def send_audio_chunk(self, audio_data: bytes) -> None:
        """
        Send audio chunk to Deepgram

        Args:
            audio_data: PCM audio data (16kHz, mono, 16-bit)
        """
        if not self._connected or not self.ws:
            raise ConnectionError("Not connected to Deepgram")

        try:
            # Deepgram expects raw PCM bytes, not base64
            await self.ws.send(audio_data)

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error sending audio chunk: {e}")
            raise

    async def receive_transcripts(self) -> AsyncIterator[TranscriptChunk]:
        """
        Receive transcript chunks from Deepgram

        Yields:
            TranscriptChunk objects as they arrive
        """
        if not self._connected or not self.ws:
            raise ConnectionError("Not connected to Deepgram")

        logger.info(f"[{self.speaker_label}] Starting to receive transcripts...")

        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)

                    # Check for metadata message
                    if "metadata" in data:
                        self._request_id = data["metadata"].get("request_id")
                        logger.info(
                            f"[{self.speaker_label}] Request ID: {self._request_id}"
                        )
                        continue

                    # Check for channel results
                    if "channel" not in data:
                        continue

                    channel = data["channel"]
                    alternatives = channel.get("alternatives", [])

                    if not alternatives:
                        continue

                    # Get the best alternative
                    best = alternatives[0]
                    text = best.get("transcript", "").strip()

                    if not text:
                        continue

                    # Determine if this is final or interim
                    is_final = data.get("is_final", False)
                    speech_final = data.get("speech_final", False)

                    # Deepgram considers it final if either is_final or speech_final is true
                    is_final_result = is_final or speech_final

                    # Get timestamps if available
                    start_ms = None
                    end_ms = None
                    if "start" in data:
                        start_ms = int(data["start"] * 1000)
                    if "duration" in data and start_ms is not None:
                        end_ms = start_ms + int(data["duration"] * 1000)

                    chunk = TranscriptChunk(
                        text=text,
                        is_final=is_final_result,
                        start_ms=start_ms,
                        end_ms=end_ms
                    )

                    log_level = "FINAL" if is_final_result else "PARTIAL"
                    logger_func = logger.info if is_final_result else logger.debug
                    logger_func(f"[{self.speaker_label}] [{log_level}] {text}")

                    yield chunk

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
                # Send close message to Deepgram
                close_message = json.dumps({"type": "CloseStream"})
                await self.ws.send(close_message)
                await asyncio.sleep(0.1)  # Give Deepgram time to process

                await self.ws.close()
                logger.info(f"[{self.speaker_label}] Disconnected from Deepgram")
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
    def request_id(self) -> Optional[str]:
        """Get current request ID"""
        return self._request_id
