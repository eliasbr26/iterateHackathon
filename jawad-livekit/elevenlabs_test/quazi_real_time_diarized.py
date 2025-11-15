import os
import time
from io import BytesIO

import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# 1) Load ElevenLabs API key
load_dotenv()
api_key = os.getenv("ELEVENLABS_API_KEY")
if not api_key:
    raise ValueError("ELEVENLABS_API_KEY is not defined in .env")

client = ElevenLabs(api_key=api_key)

# 2) Audio parameters
SAMPLE_RATE = 16000       # 16 kHz sufficient for voice
CHUNK_DURATION = 10        # duration of each "quasi real-time" chunk in seconds

def record_chunk():
    """
    Record CHUNK_DURATION seconds from the microphone
    and return a WAV buffer in memory.
    """
    print(f"\n🎙️ Recording a {CHUNK_DURATION} second chunk...")
    audio = sd.rec(
        int(CHUNK_DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16'
    )
    sd.wait()
    print("✅ Chunk recorded.")

    # Put in memory for API
    wav_bytes = BytesIO()
    wav_write(wav_bytes, SAMPLE_RATE, audio)
    wav_bytes.seek(0)
    return wav_bytes

def transcribe_with_diarization(wav_bytes, language_code="fra"):
    """
    Send audio to ElevenLabs and return the transcription object
    with diarization enabled.
    """
    transcription = client.speech_to_text.convert(
        file=wav_bytes,
        model_id="scribe_v1",
        tag_audio_events=False,
        language_code=language_code,  # "fra" for French, "eng" for English
        diarize=True,
    )
    return transcription

def display_transcription_by_speaker(transcription):
    """
    Display transcription trying to separate by speaker.
    We start simple: we use transcription.words if available.
    """
    print("\n=== CHUNK TRANSCRIPTION ===")

    # Try to access transcription.words (list of words with speaker)
    words = getattr(transcription, "words", None)

    if words:
        current_speaker = None
        current_words = []

        for w in words:
            # Depending on SDK, the attribute might be called speaker or speaker_id
            speaker = getattr(w, "speaker", getattr(w, "speaker_id", "UNKNOWN"))
            text = getattr(w, "text", "")

            if speaker != current_speaker and current_words:
                # Display the previous speaker's sentence
                print(f"[{current_speaker}] {' '.join(current_words)}")
                current_words = []

            current_speaker = speaker
            current_words.append(text)

        # Display the last speaker
        if current_words:
            print(f"[{current_speaker}] {' '.join(current_words)}")

    else:
        # If we don't have per-word detail, display at least the global text
        try:
            print(transcription.text)
        except AttributeError:
            print("Unable to read transcription.text, here is the raw object:")
            print(transcription)

def main():
    print("✅ Quasi real-time + speaker detection (diarization).")
    print("Have two people (interviewer + candidate) speak in front of the Mac.")
    print("Ctrl+C to stop.\n")

    try:
        while True:
            # 1) Record a small chunk
            wav_bytes = record_chunk()

            # 2) Transcribe with diarization
            print("🧠 Sending chunk to ElevenLabs...")
            try:
                transcription = transcribe_with_diarization(wav_bytes, language_code="fra")
            except Exception as e:
                print("❌ ElevenLabs error:", e)
                # Small pause to avoid spamming if error
                time.sleep(1)
                continue

            # 3) Display by speaker
            display_transcription_by_speaker(transcription)

            # (Optional) small pause between chunks
            # time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n👋 Stop requested by user. End of quasi real-time.")

if __name__ == "__main__":
    main()
