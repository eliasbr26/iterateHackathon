import os
from dotenv import load_dotenv
from io import BytesIO
import requests
from elevenlabs.client import ElevenLabs

# 1) Load key from .env
load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("ELEVENLABS_API_KEY is not defined in .env")

# 2) Create ElevenLabs client
client = ElevenLabs(api_key=api_key)

# 3) Download a small example audio file (provided by ElevenLabs)
audio_url = "https://storage.googleapis.com/eleven-public-cdn/audio/marketing/nicole.mp3"
response = requests.get(audio_url)
audio_data = BytesIO(response.content)

# 4) Call the Speech-to-Text API
transcription = client.speech_to_text.convert(
    file=audio_data,
    model_id="scribe_v1",      # transcription model
    tag_audio_events=True,     # tag laughs, etc. (optional)
    language_code="eng",       # language (you can use "fra" for French)
    diarize=True,              # detect speakers
)

# 5) Display the result

print("\n=== COMPLETE TRANSCRIPTION ===\n")

# The response is an object, not a dict:
print(transcription.text)

# If you want to see the language:
# (depending on SDK version, it could be language or language_code)
try:
    print("\nDetected language:", transcription.language_code)
except AttributeError:
    try:
        print("\nDetected language:", transcription.language)
    except AttributeError:
        print("\nUnable to find language attribute, here is the raw object:")
        print(transcription)
