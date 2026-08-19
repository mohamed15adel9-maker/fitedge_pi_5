import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly

SAMPLE_RATE = 44100
CHUNK_SIZE = 3528

# This must match the name of your dedicated microphone.
MIC_NAME = "USB PnP Sound Device"

stream = None


def find_microphone():
    devices = sd.query_devices()

    for i, device in enumerate(devices):
        if (
            device["max_input_channels"] > 0
            and MIC_NAME.lower() in device["name"].lower()
        ):
            print(
                f"Using microphone: {i} - {device['name']} "
                f"({device['default_samplerate']} Hz)"
            )
            return i

    raise RuntimeError(
        f"Could not find microphone containing '{MIC_NAME}'."
    )


def start_microphone():
    global stream

    mic = find_microphone()

    stream = sd.InputStream(
        device=mic,
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.int16,
    )

    stream.start()
    print("Sample rate:", stream.samplerate)


def stop_microphone():
    global stream

    if stream is not None:
        stream.stop()
        stream.close()
        stream = None


def get_microphone_chunk():
    chunk, overflowed = stream.read(CHUNK_SIZE)

    audio = chunk.flatten()

    # 44.1 kHz -> 16 kHz
    audio = resample_poly(audio, up=160, down=441)

    # Ensure exactly 1280 samples
    audio = audio[:1280]

    return np.clip(
        audio,
        -32768,
        32767
    ).astype(np.int16)