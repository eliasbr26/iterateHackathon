"""
Audio Pipeline - Clean batch-based implementation
Buffers audio from LiveKit and sends to ElevenLabs batch STT
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Dict, Optional
from io import BytesIO

from .models import Transcript
from .livekit_handler import LiveKitHandler, ParticipantInfo
from .elevenlabs_stt import ElevenLabsSTT
from .audio_converter import AudioConverter

logger = logging.getLogger(__name__)


class SpeakerStreamManager:
    """
    Manages audio buffering and batch transcription for a single speaker

    Simple approach:
    - Buffer audio for N seconds (default 5)
    - Send buffer to ElevenLabs batch STT
    - Put transcript in queue
    - Repeat
    """

    def __init__(
        self,
        participant_identity: str,
        speaker_label: str,
        livekit_handler: LiveKitHandler,
        elevenlabs_api_key: str,
        language: str = "en",
        buffer_duration_ms: int = 5000
    ):
        """
        Initialize speaker stream manager

        Args:
            participant_identity: LiveKit participant ID
            speaker_label: Speaker label ("recruiter" or "candidate")
            livekit_handler: LiveKit handler instance
            elevenlabs_api_key: ElevenLabs API key
            language: Language code (default: "en")
            buffer_duration_ms: Buffer duration in ms (default: 5000 = 5 seconds)
        """
        self.participant_identity = participant_identity
        self.speaker_label = speaker_label
        self.livekit_handler = livekit_handler
        self.elevenlabs_api_key = elevenlabs_api_key
        self.language = language
        self.buffer_duration_ms = buffer_duration_ms

        self.stt_client: Optional[ElevenLabsSTT] = None
        self.audio_converter = AudioConverter()
        self._running = False
        self._transcript_queue: Optional[asyncio.Queue] = None

    async def start(self) -> None:
        """Initialize STT client and queue"""
        self.stt_client = ElevenLabsSTT(
            api_key=self.elevenlabs_api_key,
            language=self.language
        )
        self._transcript_queue = asyncio.Queue()
        self._running = True
        logger.info(f"[{self.speaker_label}] Stream manager started (batch mode)")

    async def stream_audio(self) -> None:
        """
        Main audio processing loop

        1. Get audio frames from LiveKit
        2. Convert to PCM and buffer
        3. Every N seconds, send buffer to batch STT
        4. Put transcript in queue
        5. Repeat
        """
        if not self.stt_client or not self._transcript_queue:
            raise RuntimeError("Stream manager not started")

        try:
            audio_stream = self.livekit_handler.get_audio_stream(
                self.participant_identity
            )

            audio_buffer = BytesIO()
            target_buffer_size = self.audio_converter.calculate_chunk_size(
                duration_ms=self.buffer_duration_ms
            )

            logger.info(
                f"[{self.speaker_label}] Buffering {self.buffer_duration_ms}ms "
                f"per batch request"
            )

            async for audio_frame in audio_stream:
                if not self._running:
                    break

                try:
                    # Convert frame to PCM
                    pcm_data = self.audio_converter.convert_frame(audio_frame)
                    audio_buffer.write(pcm_data)

                    # When buffer is full, send to batch STT
                    if audio_buffer.tell() >= target_buffer_size:
                        buffer_bytes = audio_buffer.getvalue()

                        logger.debug(
                            f"[{self.speaker_label}] Sending {len(buffer_bytes)} bytes "
                            f"to batch STT"
                        )

                        # Transcribe buffer
                        text = await self.stt_client.transcribe_pcm(
                            buffer_bytes,
                            speaker=self.speaker_label
                        )

                        # If we got text, create transcript and queue it
                        if text:
                            transcript = Transcript(
                                text=text,
                                speaker=self.speaker_label,
                                start_ms=None,
                                end_ms=None,
                                is_final=True
                            )
                            await self._transcript_queue.put(transcript)

                        # Reset buffer for next window
                        audio_buffer = BytesIO()

                except Exception as e:
                    logger.error(f"[{self.speaker_label}] Error processing frame: {e}")

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error in audio streaming: {e}")
            raise
        finally:
            # Signal end of transcripts
            await self._transcript_queue.put(None)
            logger.info(f"[{self.speaker_label}] Audio streaming stopped")

    async def receive_transcripts(self) -> AsyncIterator[Transcript]:
        """
        Yield transcripts from queue as they become available

        This method simply reads from the queue that stream_audio() fills.
        """
        if not self._transcript_queue:
            raise RuntimeError("Transcript queue not initialized")

        try:
            while True:
                transcript = await self._transcript_queue.get()

                if transcript is None:
                    logger.info(f"[{self.speaker_label}] End of transcript stream")
                    break

                yield transcript

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error receiving transcripts: {e}")
            raise

    async def stop(self) -> None:
        """Stop streaming and close STT client"""
        self._running = False
        if self.stt_client:
            await self.stt_client.close()
        logger.info(f"[{self.speaker_label}] Stream manager stopped")


class AudioPipeline:
    """
    Main audio pipeline orchestrator

    Connects to LiveKit, captures audio from participants,
    sends to ElevenLabs batch STT, and yields transcripts.
    """

    def __init__(
        self,
        livekit_url: str,
        livekit_room: str,
        livekit_token: str,
        elevenlabs_api_key: str,
        language: str = "en",
        recruiter_identity: str = "interviewer",
        candidate_identity: str = "candidate",
        buffer_duration_ms: int = 5000
    ):
        """
        Initialize audio pipeline

        Args:
            livekit_url: LiveKit server URL
            livekit_room: LiveKit room name
            livekit_token: LiveKit JWT token
            elevenlabs_api_key: ElevenLabs API key
            language: Language code (default: "en")
            recruiter_identity: Identity string for recruiter
            candidate_identity: Identity string for candidate
            buffer_duration_ms: Buffer duration for batch STT (default: 5000ms)
        """
        self.livekit_url = livekit_url
        self.livekit_room = livekit_room
        self.livekit_token = livekit_token
        self.elevenlabs_api_key = elevenlabs_api_key
        self.language = language
        self.recruiter_identity = recruiter_identity
        self.candidate_identity = candidate_identity
        self.buffer_duration_ms = buffer_duration_ms

        self.livekit_handler: Optional[LiveKitHandler] = None
        self.stream_managers: Dict[str, SpeakerStreamManager] = {}
        self._running = False

    async def _initialize(self) -> None:
        """Initialize LiveKit connection and wait for participants"""
        logger.info("Initializing audio pipeline...")

        # Connect to LiveKit
        self.livekit_handler = LiveKitHandler(
            room_url=self.livekit_url,
            room_name=self.livekit_room,
            token=self.livekit_token,
            recruiter_identity=self.recruiter_identity,
            candidate_identity=self.candidate_identity
        )
        await self.livekit_handler.connect()

        # Wait for participants to join
        logger.info("Waiting for participants...")
        max_wait = 30
        start_time = time.time()

        while time.time() - start_time < max_wait:
            participants = self.livekit_handler.get_all_participants()
            if len(participants) >= 2:
                logger.info(f"Found {len(participants)} participants")
                break
            await asyncio.sleep(0.5)

        participants = self.livekit_handler.get_all_participants()
        if len(participants) < 2:
            logger.warning(
                f"Only {len(participants)} participant(s) found. "
                "Expected at least 2 (recruiter and candidate)"
            )

        # Initialize stream managers for each participant
        for identity, participant_info in participants.items():
            manager = SpeakerStreamManager(
                participant_identity=identity,
                speaker_label=participant_info.speaker_label,
                livekit_handler=self.livekit_handler,
                elevenlabs_api_key=self.elevenlabs_api_key,
                language=self.language,
                buffer_duration_ms=self.buffer_duration_ms
            )
            await manager.start()
            self.stream_managers[identity] = manager

        logger.info(f"Initialized {len(self.stream_managers)} stream managers")
        self._running = True

    async def _stream_all_audio(self) -> None:
        """Start audio streaming tasks for all participants"""
        tasks = []
        for manager in self.stream_managers.values():
            task = asyncio.create_task(manager.stream_audio())
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in audio streaming tasks: {e}")
            for task in tasks:
                if not task.done():
                    task.cancel()

    async def start_transcription(self) -> AsyncIterator[Transcript]:
        """
        Start real-time transcription

        Yields:
            Transcript objects with speaker labels

        Example:
            ```python
            pipeline = AudioPipeline(...)
            async for transcript in pipeline.start_transcription():
                print(f"[{transcript.speaker}] {transcript.text}")
            ```
        """
        try:
            # Initialize connections
            await self._initialize()

            # Start audio streaming in background
            audio_streaming_task = asyncio.create_task(self._stream_all_audio())

            # Create queues and start receiver tasks
            transcript_queues: Dict[str, asyncio.Queue] = {}
            receiver_tasks = []

            async def receive_and_queue(manager: SpeakerStreamManager, queue: asyncio.Queue):
                """Receive transcripts and put in queue"""
                try:
                    async for transcript in manager.receive_transcripts():
                        await queue.put(transcript)
                except Exception as e:
                    logger.error(f"Error in transcript receiver: {e}")
                finally:
                    await queue.put(None)

            for manager in self.stream_managers.values():
                queue = asyncio.Queue()
                transcript_queues[manager.speaker_label] = queue
                task = asyncio.create_task(receive_and_queue(manager, queue))
                receiver_tasks.append(task)

            # Yield transcripts as they arrive
            active_queues = set(transcript_queues.keys())

            while active_queues and self._running:
                for speaker_label in list(active_queues):
                    queue = transcript_queues[speaker_label]

                    try:
                        transcript = queue.get_nowait()

                        if transcript is None:
                            active_queues.remove(speaker_label)
                            logger.info(f"[{speaker_label}] Stream ended")
                        else:
                            yield transcript

                    except asyncio.QueueEmpty:
                        pass

                await asyncio.sleep(0.01)

            # Cleanup
            logger.info("Transcription ended, cleaning up...")

            audio_streaming_task.cancel()
            for task in receiver_tasks:
                if not task.done():
                    task.cancel()

            try:
                await audio_streaming_task
            except asyncio.CancelledError:
                pass

            for task in receiver_tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Error in audio pipeline: {e}")
            raise
        finally:
            await self.cleanup()

    async def cleanup(self) -> None:
        """Clean up all connections and resources"""
        self._running = False

        logger.info("Cleaning up audio pipeline...")

        for manager in self.stream_managers.values():
            try:
                await manager.stop()
            except Exception as e:
                logger.error(f"Error stopping stream manager: {e}")

        if self.livekit_handler:
            try:
                await self.livekit_handler.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting from LiveKit: {e}")

        logger.info("Audio pipeline cleanup complete")

    async def stop(self) -> None:
        """Stop the pipeline"""
        self._running = False
        await self.cleanup()
