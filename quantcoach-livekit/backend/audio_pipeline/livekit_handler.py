"""
LiveKit connection and audio track management
"""

import asyncio
import logging
from typing import Dict, Optional, AsyncIterator
from dataclasses import dataclass

from livekit import rtc

logger = logging.getLogger(__name__)


@dataclass
class ParticipantInfo:
    """Information about a LiveKit participant"""
    identity: str
    speaker_label: str  # "recruiter", "candidate", or "agent"
    audio_track: Optional[rtc.RemoteAudioTrack] = None


class LiveKitHandler:
    """Manages LiveKit room connection and audio tracks"""

    def __init__(
        self,
        room_url: str,
        room_name: str,
        token: str,
        recruiter_identity: str = "interviewer",
        candidate_identity: str = "candidate"
    ):
        """
        Initialize LiveKit handler

        Args:
            room_url: LiveKit server URL
            room_name: Name of the room to join
            token: JWT token for authentication
            recruiter_identity: Identity string for recruiter participant
            candidate_identity: Identity string for candidate participant
        """
        self.room_url = room_url
        self.room_name = room_name
        self.token = token
        self.recruiter_identity = recruiter_identity
        self.candidate_identity = candidate_identity

        self.room: Optional[rtc.Room] = None
        self.participants: Dict[str, ParticipantInfo] = {}
        self._connected = False

    async def connect(self) -> None:
        """Connect to LiveKit room as a bot"""
        if self._connected:
            logger.warning("Already connected to LiveKit room")
            return

        self.room = rtc.Room()

        # Set up event handlers
        @self.room.on("participant_connected")
        def on_participant_connected(participant: rtc.RemoteParticipant):
            logger.info(f"✅ Participant connected: {participant.identity}")
            self._register_participant(participant)

        @self.room.on("participant_disconnected")
        def on_participant_disconnected(participant: rtc.RemoteParticipant):
            logger.info(f"🚪 Participant disconnected: {participant.identity}")
            if participant.identity in self.participants:
                del self.participants[participant.identity]

        @self.room.on("track_published")
        def on_track_published(
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant
        ):
            logger.info(
                f"📢 Track published: {publication.sid} by {participant.identity}"
            )

        @self.room.on("track_subscribed")
        def on_track_subscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant
        ):
            logger.info(f"🎧 Track subscribed: {track.sid} by {participant.identity}")
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                self._handle_audio_track(participant, track)

        @self.room.on("track_unsubscribed")
        def on_track_unsubscribed(
            track: rtc.Track,
            publication: rtc.RemoteTrackPublication,
            participant: rtc.RemoteParticipant
        ):
            logger.info(f"🔇 Track unsubscribed: {track.sid} by {participant.identity}")
            if participant.identity in self.participants:
                self.participants[participant.identity].audio_track = None

        # Connect to room
        logger.info(f"🔌 Connecting to LiveKit room: {self.room_name}")
        await self.room.connect(self.room_url, self.token)
        self._connected = True
        logger.info("✅ Connected to LiveKit room")

        # Register existing participants
        for participant in self.room.remote_participants.values():
            self._register_participant(participant)

    def _register_participant(self, participant: rtc.RemoteParticipant) -> None:
        """Register a participant and determine their speaker label"""
        speaker_label = self._get_speaker_label(participant.identity)

        participant_info = ParticipantInfo(
            identity=participant.identity,
            speaker_label=speaker_label
        )

        self.participants[participant.identity] = participant_info
        logger.info(f"✅ Registered participant {participant.identity} as {speaker_label}")

    def _get_speaker_label(self, identity: str) -> str:
        """Determine speaker label from participant identity"""
        identity_lower = identity.lower()

        # Filter out bot/agent participants
        if identity_lower.startswith("audio-agent-") or identity_lower.startswith("agent-simple-") or "agent" in identity_lower:
            return "agent"

        if self.recruiter_identity.lower() in identity_lower or "interviewer" in identity_lower:
            return "recruiter"
        elif self.candidate_identity.lower() in identity_lower or "candidate" in identity_lower:
            return "candidate"
        else:
            # Default fallback based on order of joining
            existing_labels = {p.speaker_label for p in self.participants.values()}
            if "recruiter" not in existing_labels:
                return "recruiter"
            return "candidate"

    def _handle_audio_track(
        self,
        participant: rtc.RemoteParticipant,
        track: rtc.Track
    ) -> None:
        """Handle new audio track from participant"""
        if participant.identity in self.participants:
            self.participants[participant.identity].audio_track = track
            logger.info(
                f"🎤 Audio track registered for {participant.identity} "
                f"({self.participants[participant.identity].speaker_label})"
            )

    async def get_audio_stream(
        self,
        participant_identity: str
    ) -> AsyncIterator[rtc.AudioFrame]:
        """
        Get audio frames from a specific participant

        Args:
            participant_identity: Identity of the participant

        Yields:
            AudioFrame objects from the participant's audio track
        """
        if participant_identity not in self.participants:
            raise ValueError(f"Participant {participant_identity} not found")

        participant_info = self.participants[participant_identity]

        # Wait for audio track to be available
        max_wait = 60  # seconds
        waited = 0
        while participant_info.audio_track is None and waited < max_wait:
            await asyncio.sleep(0.1)
            waited += 0.1

        if participant_info.audio_track is None:
            raise TimeoutError(
                f"Audio track not available for {participant_identity} after {max_wait}s"
            )

        track = participant_info.audio_track
        logger.info(f"🎵 Starting audio stream for {participant_identity}")

        # Stream audio frames
        async for frame_event in rtc.AudioStream(track):
            yield frame_event.frame

    def get_participant_speaker_label(self, identity: str) -> Optional[str]:
        """Get speaker label for a participant"""
        if identity in self.participants:
            return self.participants[identity].speaker_label
        return None

    def get_all_participants(self) -> Dict[str, ParticipantInfo]:
        """Get all registered participants"""
        return self.participants.copy()

    async def disconnect(self) -> None:
        """Disconnect from LiveKit room"""
        if self.room and self._connected:
            await self.room.disconnect()
            self._connected = False
            logger.info("🔌 Disconnected from LiveKit room")

    @property
    def is_connected(self) -> bool:
        """Check if connected to room"""
        return self._connected
