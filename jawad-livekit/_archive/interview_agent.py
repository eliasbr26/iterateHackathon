"""
LiveKit Interview Analysis Agent

This agent joins a LiveKit room and listens to the conversation between
interviewer and candidate. It performs real-time speech-to-text and can
analyze sentiment/communication patterns.
"""

import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import deepgram, openai, silero

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InterviewAnalyzer:
    """Handles real-time interview analysis"""

    def __init__(self):
        self.transcripts = []
        self.participants = {}

    async def on_speech_detected(self, text: str, participant_identity: str):
        """Process transcribed speech from participants"""
        logger.info(f"[{participant_identity}]: {text}")

        # Store transcript with participant info
        self.transcripts.append({
            "participant": participant_identity,
            "text": text,
            "timestamp": asyncio.get_event_loop().time()
        })

        # Here you can add sentiment analysis or other processing
        # For now, we just log it

    def get_analysis_summary(self) -> dict:
        """Return analysis summary of the interview"""
        return {
            "total_transcripts": len(self.transcripts),
            "participants": list(self.participants.keys()),
            "transcripts": self.transcripts
        }


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the LiveKit agent.
    This function is called when the agent is assigned to a room.
    """
    logger.info(f"Starting interview agent for room: {ctx.room.name}")

    # Initialize the analyzer
    analyzer = InterviewAnalyzer()

    # Connect to the room
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info(f"Connected to room: {ctx.room.name}")

    # Create a simple assistant that listens but doesn't speak
    # This is a "silent observer" agent
    assistant = VoicePipelineAgent(
        vad=silero.VAD.load(),
        stt=deepgram.STT(model="nova-2"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=None,  # No TTS - we're just listening
        chat_ctx=llm.ChatContext().append(
            role="system",
            text=(
                "You are an interview analysis assistant. "
                "You listen to conversations and provide insights. "
                "You do not speak during the interview."
            ),
        ),
    )

    # Set up event handlers for room events
    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant connected: {participant.identity}")
        analyzer.participants[participant.identity] = participant

    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(participant: rtc.RemoteParticipant):
        logger.info(f"Participant disconnected: {participant.identity}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info(f"Track subscribed: {track.kind} from {participant.identity}")

        if track.kind == rtc.TrackKind.KIND_AUDIO:
            # Process audio track for transcription
            audio_stream = rtc.AudioStream(track)
            asyncio.create_task(
                process_audio_stream(audio_stream, participant.identity, analyzer)
            )

    # Start the assistant (it will listen to the room)
    assistant.start(ctx.room)

    # Keep the agent running
    await asyncio.sleep(3600)  # Run for 1 hour max, adjust as needed

    # Print final analysis
    logger.info("Interview session ended")
    summary = analyzer.get_analysis_summary()
    logger.info(f"Analysis summary: {summary}")


async def process_audio_stream(
    audio_stream: rtc.AudioStream,
    participant_identity: str,
    analyzer: InterviewAnalyzer
):
    """
    Process audio stream from a participant
    This is a placeholder - actual STT will be handled by the assistant
    """
    async for audio_frame in audio_stream:
        # Audio processing happens in the VoicePipelineAgent
        # This is just for demonstration
        pass


def main():
    """Run the agent worker"""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            # The agent will only be assigned to rooms, it won't join automatically
            request_fnc=None,
        )
    )


if __name__ == "__main__":
    main()
