"""
Audio Pipeline for LiveKit + ElevenLabs Batch STT

Clean batch-based implementation for interview transcription.

Main components:
- AudioPipeline: Main orchestrator
- Transcript: Dataclass for transcript results
- LiveKitHandler: LiveKit connection management
- ElevenLabsSTT: ElevenLabs batch STT client
- AudioConverter: Audio format conversion utilities
"""

from .models import Transcript
from .pipeline import AudioPipeline
from .livekit_handler import LiveKitHandler
from .elevenlabs_stt import ElevenLabsSTT
from .audio_converter import AudioConverter
from .logging_config import setup_logging, setup_colored_logging

__version__ = "2.0.0"

__all__ = [
    "Transcript",
    "AudioPipeline",
    "LiveKitHandler",
    "ElevenLabsSTT",
    "AudioConverter",
    "setup_logging",
    "setup_colored_logging"
]
