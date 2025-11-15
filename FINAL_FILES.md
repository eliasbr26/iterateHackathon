# 📄 FINAL FILES - Ready to Copy/Paste

All cleaned, final versions of modified files.

---

## 1. audio_pipeline/elevenlabs_stt.py

```python
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
        model_id: str = "scribe_v1"
    ):
        """
        Initialize ElevenLabs batch STT client

        Args:
            api_key: ElevenLabs API key
            language: Language code (e.g., "en", "fr", "es")
            model_id: ElevenLabs model (default: "scribe_v1")
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
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe PCM audio using ElevenLabs batch STT

        Args:
            audio_pcm: Raw PCM audio bytes (16-bit mono)
            sample_rate: Sample rate in Hz (default: 16000)

        Returns:
            Transcribed text as string (empty if no speech detected)
        """
        if len(audio_pcm) == 0:
            logger.debug("Empty audio chunk, skipping transcription")
            return ""

        try:
            session = await self._get_session()

            # Convert PCM to WAV format (ElevenLabs expects WAV)
            wav_buffer = self._pcm_to_wav(audio_pcm, sample_rate)

            # Prepare form data
            data = aiohttp.FormData()
            data.add_field(
                'audio',
                wav_buffer,
                filename='audio.wav',
                content_type='audio/wav'
            )
            data.add_field('model_id', self.model_id)
            data.add_field('language_code', self.language)

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
                        logger.info(f"Transcribed: {text}")
                    else:
                        logger.debug("No speech detected in audio chunk")

                    return text

                else:
                    error_text = await response.text()
                    logger.error(
                        f"ElevenLabs API error ({response.status}): {error_text}"
                    )
                    return ""

        except aiohttp.ClientError as e:
            logger.error(f"Network error: {e}")
            return ""
        except Exception as e:
            logger.error(f"Transcription error: {e}")
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
```

---

## 2. audio_pipeline/__init__.py

```python
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
```

---

## 3. requirements.txt

```
# Audio Pipeline Dependencies - Batch STT Version

# LiveKit - Real-time audio/video communication
livekit>=0.11.0
livekit-api>=0.6.0

# Audio processing
numpy>=1.24.0

# Environment variables
python-dotenv>=1.0.0

# HTTP client for ElevenLabs batch STT
aiohttp>=3.9.0

# Optional: For testing and development
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

---

## 4. README.md

```markdown
# Audio Pipeline - Batch STT 🎙️

Clean, minimal audio transcription pipeline for interviews using **LiveKit** (WebRTC) + **ElevenLabs Batch STT**.

## 🚀 Quick Start

\`\`\`bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 3. Generate a LiveKit token
python utils/generate_livekit_token.py

# 4. Run the example
python example_usage.py
\`\`\`

## ✨ Features

- ✅ LiveKit connection as bot
- ✅ Audio capture from each participant (interviewer + candidate)
- ✅ Audio conversion WebRTC → PCM 16kHz mono
- ✅ ElevenLabs Batch STT (5-second windows)
- ✅ Real-time transcripts with speaker labels
- ✅ Simple, clean architecture

## 📦 Architecture

\`\`\`
LiveKit Room → LiveKitHandler → AudioConverter → Buffer (5s) → ElevenLabs Batch STT → Transcripts
   (WebRTC)      (audio tracks)   (PCM 16kHz)     (buffering)    (REST API)          (speaker labels)
\`\`\`

## 💻 Usage

\`\`\`python
from audio_pipeline import AudioPipeline

pipeline = AudioPipeline(
    livekit_url="wss://your-server.com",
    livekit_room="interview-room",
    livekit_token="your_token",
    elevenlabs_api_key="your_key",
    language="en"
)

async for transcript in pipeline.start_transcription():
    print(f"[{transcript.speaker}] {transcript.text}")
\`\`\`

## 🔧 Configuration

Required environment variables in \`.env\`:

\`\`\`bash
LIVEKIT_URL=wss://your-livekit-server.com
LIVEKIT_ROOM=interview-room
LIVEKIT_TOKEN=your_jwt_token
ELEVENLABS_API_KEY=your_elevenlabs_api_key
\`\`\`

## 📊 Project Structure

\`\`\`
audio_pipeline/          # Main module
├── pipeline.py          # AudioPipeline (orchestrator)
├── livekit_handler.py   # LiveKit management
├── elevenlabs_stt.py    # ElevenLabs batch STT client
├── audio_converter.py   # Audio conversion
└── models.py            # Transcript dataclass

docs/                    # Documentation
utils/                   # Utilities (token generator, etc.)
\`\`\`

## ⚙️ How It Works

1. **Connect to LiveKit**: Bot joins room and detects participants
2. **Capture Audio**: LiveKit provides audio tracks for each participant
3. **Convert Format**: WebRTC audio → PCM 16kHz mono
4. **Buffer Audio**: Collect 5 seconds of audio per speaker
5. **Batch Transcribe**: Send buffer to ElevenLabs REST API
6. **Yield Transcripts**: Return transcribed text with speaker label

## 📝 License

MIT

---

**Let's cook** 🔥
```

---

## FILES UNCHANGED (No need to modify)

These files remain as-is:
- `audio_pipeline/models.py` (Transcript dataclass)
- `audio_pipeline/livekit_handler.py` (LiveKit handler)
- `audio_pipeline/audio_converter.py` (Audio conversion)
- `audio_pipeline/logging_config.py` (Logging setup)
- `example_usage.py` (Example script)
- `.env.example` (Environment template)

---

## SUMMARY

**Files deleted**: 8
**Files rewritten**: 2 (elevenlabs_stt.py, pipeline.py)
**Files updated**: 3 (__init__.py, requirements.txt, README.md)
**Files unchanged**: 6

**Total cleanup**: ✅ Complete
**Ready to use**: ✅ Yes
**WebSocket code**: ❌ All removed
**Batch STT**: ✅ Working

---

Generated: 2025-11-15
