from pathlib import Path
from piper import PiperVoice
import wave
import winsound

VOICE_PATH = Path("tts/voices/en_US-john-medium.onnx")

print("Loading Piper voice...")
voice = PiperVoice.load(str(VOICE_PATH))


def speak(text):
    output_file = "audio/response.wav"

    with wave.open(output_file, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    winsound.PlaySound(output_file, winsound.SND_FILENAME)

    return output_file