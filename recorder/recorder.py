import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy.signal import resample_poly

def record_audio(filename="audio/recording.wav", duration=5):
    RECORD_RATE = 44100
    TARGET_RATE = 16000

    print("Recording... Speak now!")
    print("Default devices:", sd.default.device)
    print(sd.query_devices())
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            temp = i
            break

    print("Recording from device:", temp)

    audio = sd.rec(
        int(duration * RECORD_RATE),
        samplerate=RECORD_RATE,
        device=temp,          # USB PnP microphone
        channels=1,
        dtype=np.int16
    )

    sd.wait()

    # Convert to mono 1D array
    audio = audio.flatten()

    # Resample 44.1 kHz -> 16 kHz
    audio = resample_poly(audio, up=160, down=441)

    # Convert to float32 in [-1, 1] (most STT models expect this)
    audio = audio.astype(np.float32) / 32768.0

    sf.write(filename, audio, TARGET_RATE)

    print(f"Saved recording to {filename}")

    return filename