
from pathlib import Path
from piper import PiperVoice
import wave
import subprocess

VOICE_PATH = Path("tts/voices/en_US-john-medium.onnx")

print("Loading Piper voice...")
voice = PiperVoice.load(str(VOICE_PATH))


def speak(text):
    output_file = "audio/response.wav"

    # Generate speech
    with wave.open(output_file, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    subprocess.run(["pw-play", output_file], check=True)

    return output_file

