"""
Main audio pipeline orchestrator
Connects LiveKit audio streams to ElevenLabs STT and yields transcripts
"""

import asyncio
import logging
import time
from typing import AsyncIterator, Dict, Optional, Set
from io import BytesIO

from .models import Transcript
from .livekit_handler import LiveKitHandler, ParticipantInfo
from .elevenlabs_stt import ElevenLabsSTT
from .deepgram_stt import DeepgramSTT
from .elevenlabs_stt import TranscriptChunk
from .audio_converter import AudioConverter

logger = logging.getLogger(__name__)


class SpeakerStreamManager:
    """Manages audio streaming and transcription for a single speaker"""

    def __init__(
        self,
        participant_identity: str,
        speaker_label: str,
        livekit_handler: LiveKitHandler,
        stt_api_key: str,
        language: str = "en",
        stt_provider: str = "deepgram"
    ):
        self.participant_identity = participant_identity
        self.speaker_label = speaker_label
        self.livekit_handler = livekit_handler
        self.stt_api_key = stt_api_key
        self.language = language
        self.stt_provider = stt_provider

        self.stt_client = None
        self.audio_converter = AudioConverter()
        self._running = False

    async def start(self) -> None:
        """Initialize STT connection"""
        if self.stt_provider == "deepgram":
            self.stt_client = DeepgramSTT(
                api_key=self.stt_api_key,
                speaker_label=self.speaker_label,
                language=self.language
            )
        elif self.stt_provider == "elevenlabs":
            self.stt_client = ElevenLabsSTT(
                api_key=self.stt_api_key,
                speaker_label=self.speaker_label,
                language=self.language
            )
        else:
            raise ValueError(f"Unknown STT provider: {self.stt_provider}")

        await self.stt_client.connect()
        self._running = True
        logger.info(f"[{self.speaker_label}] Stream manager started with {self.stt_provider}")

    async def stream_audio(self) -> None:
        """Stream audio from LiveKit to ElevenLabs"""
        if not self.stt_client:
            raise RuntimeError("STT client not initialized")

        try:
            audio_stream = self.livekit_handler.get_audio_stream(
                self.participant_identity
            )

            chunk_buffer = BytesIO()
            target_chunk_size = self.audio_converter.calculate_chunk_size(
                duration_ms=200  # Send 200ms chunks (more data = better accuracy)
            )

            async for audio_frame in audio_stream:
                if not self._running:
                    break

                try:
                    # Convert frame to PCM
                    pcm_data = self.audio_converter.convert_frame(audio_frame)

                    # Buffer audio chunks
                    chunk_buffer.write(pcm_data)

                    # Send when buffer reaches target size
                    if chunk_buffer.tell() >= target_chunk_size:
                        audio_chunk = chunk_buffer.getvalue()
                        await self.stt_client.send_audio_chunk(audio_chunk)

                        # Reset buffer
                        chunk_buffer = BytesIO()

                except Exception as e:
                    logger.error(
                        f"[{self.speaker_label}] Error processing audio frame: {e}"
                    )

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error in audio streaming: {e}")
            raise
        finally:
            logger.info(f"[{self.speaker_label}] Audio streaming stopped")

    async def receive_transcripts(self) -> AsyncIterator[Transcript]:
        """Receive and yield transcripts from ElevenLabs"""
        if not self.stt_client:
            raise RuntimeError("STT client not initialized")

        try:
            async for chunk in self.stt_client.receive_transcripts():
                transcript = Transcript(
                    text=chunk.text,
                    speaker=self.speaker_label,
                    start_ms=chunk.start_ms,
                    end_ms=chunk.end_ms,
                    is_final=chunk.is_final
                )
                yield transcript

        except Exception as e:
            logger.error(f"[{self.speaker_label}] Error receiving transcripts: {e}")
            raise

    async def stop(self) -> None:
        """Stop streaming and disconnect"""
        self._running = False
        if self.stt_client:
            await self.stt_client.disconnect()
        logger.info(f"[{self.speaker_label}] Stream manager stopped")


class AudioPipeline:
    """
    Main audio pipeline for real-time transcription

    Connects to LiveKit room, streams audio to ElevenLabs STT,
    and yields transcripts with speaker labels
    """

    def __init__(
        self,
        livekit_url: str,
        livekit_room: str,
        livekit_token: str,
        stt_api_key: str,
        language: str = "en",
        recruiter_identity: str = "interviewer",
        candidate_identity: str = "candidate",
        stt_provider: str = "deepgram"
    ):
        """
        Initialize audio pipeline

        Args:
            livekit_url: LiveKit server URL
            livekit_room: LiveKit room name
            livekit_token: LiveKit JWT token
            stt_api_key: STT API key (Deepgram or ElevenLabs)
            language: Language code (default: "en")
            recruiter_identity: Identity string for recruiter
            candidate_identity: Identity string for candidate
            stt_provider: STT provider - "deepgram" or "elevenlabs" (default: "deepgram")
        """
        self.livekit_url = livekit_url
        self.livekit_room = livekit_room
        self.livekit_token = livekit_token
        self.stt_api_key = stt_api_key
        self.language = language
        self.recruiter_identity = recruiter_identity
        self.candidate_identity = candidate_identity
        self.stt_provider = stt_provider

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
        max_wait = 60  # seconds (increased from 30s)
        start_time = time.time()

        while time.time() - start_time < max_wait:
            participants = self.livekit_handler.get_all_participants()

            if len(participants) >= 2:
                logger.info(f"Found {len(participants)} participants")
                # Wait an additional 5 seconds for audio tracks to be fully ready
                logger.info("Waiting 5s for audio tracks to stabilize...")
                await asyncio.sleep(5)
                break

            await asyncio.sleep(0.5)

        participants = self.livekit_handler.get_all_participants()

        # Validate participant count
        human_participants = {
            identity: info for identity, info in participants.items()
            if info.speaker_label != "agent"
        }
        if len(human_participants) < 2:
            logger.warning(
                f"Only {len(human_participants)} human participant(s) found. "
                "Expected at least 2 (recruiter and candidate)"
            )

        # Validate audio tracks for human participants
        logger.info("Validating audio tracks for participants...")
        for identity, participant_info in human_participants.items():
            if participant_info.audio_track is None:
                logger.warning(
                    f"⚠️  Participant {identity} ({participant_info.speaker_label}) "
                    "has no audio track - may timeout during streaming"
                )
            else:
                logger.info(
                    f"✓ Participant {identity} ({participant_info.speaker_label}) "
                    "has audio track ready"
                )

        # Initialize stream managers for each participant
        for identity, participant_info in participants.items():
            # Skip agent participants (bots that join for monitoring/transcription)
            if participant_info.speaker_label == "agent":
                logger.info(f"Skipping agent participant: {identity}")
                continue

            manager = SpeakerStreamManager(
                participant_identity=identity,
                speaker_label=participant_info.speaker_label,
                livekit_handler=self.livekit_handler,
                stt_api_key=self.stt_api_key,
                language=self.language,
                stt_provider=self.stt_provider
            )
            await manager.start()
            self.stream_managers[identity] = manager

        logger.info(f"Initialized {len(self.stream_managers)} stream managers (skipped agents)")
        self._running = True

    async def _stream_with_error_handling(self, manager) -> None:
        """
        Stream audio with graceful error handling for individual participants

        This prevents one participant's failure from crashing the entire pipeline
        """
        try:
            await manager.stream_audio()
        except TimeoutError as e:
            logger.warning(
                f"Timeout for participant {manager.participant_identity}: {e} "
                "- continuing with other participants"
            )
        except Exception as e:
            logger.error(
                f"Error streaming audio for {manager.participant_identity}: {e}",
                exc_info=True
            )

    async def _stream_all_audio(self) -> None:
        """Start audio streaming for all participants"""
        tasks = []
        for manager in self.stream_managers.values():
            # Wrap each stream in error handling
            task = asyncio.create_task(self._stream_with_error_handling(manager))
            tasks.append(task)

        # Wait for all streaming tasks (they run indefinitely)
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in audio streaming tasks: {e}")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()

    async def start_transcription(
        self,
        audio_stream=None  # For compatibility with your interface
    ) -> AsyncIterator[Transcript]:
        """
        Start real-time transcription

        Yields:
            Transcript objects with speaker labels in real-time

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

            # Start audio streaming tasks in background
            audio_streaming_task = asyncio.create_task(self._stream_all_audio())

            # Create transcript queues for each speaker UP FRONT
            transcript_queues: Dict[str, asyncio.Queue] = {}

            # Start transcript receiving tasks
            async def receive_and_queue(manager: SpeakerStreamManager, queue: asyncio.Queue):
                """Receive transcripts and put them in queue"""
                try:
                    async for transcript in manager.receive_transcripts():
                        await queue.put(transcript)
                except Exception as e:
                    logger.error(
                        f"[{manager.speaker_label}] Error in transcript receiver: {e}"
                    )
                finally:
                    await queue.put(None)  # Sentinel value

            # Create queues and start receiver tasks
            receiver_tasks = []
            for manager in self.stream_managers.values():
                queue = asyncio.Queue()
                transcript_queues[manager.speaker_label] = queue
                task = asyncio.create_task(receive_and_queue(manager, queue))
                receiver_tasks.append(task)

            # Yield transcripts as they arrive from any speaker
            active_queues = set(transcript_queues.keys())

            while active_queues and self._running:
                # Check all queues for available transcripts
                for speaker_label in list(active_queues):
                    queue = transcript_queues[speaker_label]

                    try:
                        # Try to get transcript without blocking
                        transcript = queue.get_nowait()

                        if transcript is None:
                            # Speaker stream ended
                            active_queues.remove(speaker_label)
                            logger.info(f"[{speaker_label}] Stream ended")
                        else:
                            yield transcript

                    except asyncio.QueueEmpty:
                        # No transcript available from this speaker yet
                        pass

                # Small delay to prevent busy-waiting
                await asyncio.sleep(0.01)

            # Cleanup
            logger.info("Transcription ended, cleaning up...")

            # Cancel tasks
            audio_streaming_task.cancel()
            for task in receiver_tasks:
                if not task.done():
                    task.cancel()

            # Wait for cancellation
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

        # Stop all stream managers
        for manager in self.stream_managers.values():
            try:
                await manager.stop()
            except Exception as e:
                logger.error(f"Error stopping stream manager: {e}")

        # Disconnect from LiveKit
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
