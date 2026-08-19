import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy.signal import resample_poly


MIC_NAME = "USB PnP Sound Device"


def find_microphone():
    devices = sd.query_devices()

    for i, device in enumerate(devices):
        if (
            device["max_input_channels"] > 0
            and MIC_NAME.lower() in device["name"].lower()
        ):
            print(f"Using microphone: {i} - {device['name']}")
            return i

    raise RuntimeError(
        f"Could not find microphone containing '{MIC_NAME}'."
    )


def record_audio(filename="audio/recording.wav", duration=5):
    RECORD_RATE = 44100
    TARGET_RATE = 16000

    print("Recording... Speak now!")

    mic = find_microphone()

    audio = sd.rec(
        int(duration * RECORD_RATE),
        samplerate=RECORD_RATE,
        device=mic,
        channels=1,
        dtype=np.int16
    )

    sd.wait()

    # Convert to mono 1D array
    audio = audio.flatten()

    # Resample 44.1 kHz -> 16 kHz
    audio = resample_poly(
        audio,
        up=160,
        down=441
    )

    # Convert to float32 in [-1, 1]
    audio = audio.astype(np.float32) / 32768.0

    sf.write(
        filename,
        audio,
        TARGET_RATE
    )

    print(f"Saved recording to {filename}")

    return filename