import os
from io import BytesIO

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# 1) Load API key from .env
load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("ELEVENLABS_API_KEY is not defined in .env")

client = ElevenLabs(api_key=api_key)

# 2) Recording parameters
SAMPLE_RATE = 16000   # 16 kHz, sufficient for voice
DURATION = 8          # duration in seconds (you can increase later)

print("✅ Ready to record.")
input("Press Enter and speak into the microphone for 8 seconds...")

# 3) Record from microphone
print("🎙️ Recording in progress...")
audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype='int16'
)
sd.wait()  # wait for recording to finish
print("✅ Recording complete.")

# 4) Save to a WAV file (optional but useful for debugging)
wav_filename = "recording_from_mic.wav"
wav_write(wav_filename, SAMPLE_RATE, audio)
print(f"💾 Audio saved to {wav_filename}")

# 5) Prepare data for API (in memory)
wav_bytes = BytesIO()
wav_write(wav_bytes, SAMPLE_RATE, audio)
wav_bytes.seek(0)

# 6) Call ElevenLabs Speech-to-Text API
print("🧠 Sending to ElevenLabs for transcription...")
transcription = client.speech_to_text.convert(
    file=wav_bytes,
    model_id="scribe_v1",
    tag_audio_events=True,
    language_code="fra",   # use "fra" for French, "eng" for English
    diarize=False,         # here a single source (you)
)

# 7) Display transcribed text
print("\n=== COMPLETE TRANSCRIPTION ===\n")
print(transcription.text)

# If you want to see more details, you can do:
# print(transcription)
