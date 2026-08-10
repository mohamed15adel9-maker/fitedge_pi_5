import sounddevice as sd
import numpy as np

SAMPLE_RATE = 44100
CHUNK_SIZE = 3528

stream = None

def start_microphone():
    global stream

    devices = sd.query_devices()

    mic = None
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            print(f"Using microphone: {i} - {d['name']}")
            mic = i
            break

    if mic is None:
        raise RuntimeError("No input microphone found.")

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


from scipy.signal import resample_poly

from scipy.signal import resample_poly
import numpy as np

def get_microphone_chunk():
    chunk, overflowed = stream.read(CHUNK_SIZE)

    # Keep raw int16 PCM
    audio = chunk.flatten()

    # Resample 44.1 kHz -> 16 kHz
    audio = resample_poly(audio, up=160, down=441)

    # Ensure exactly 1280 samples
    audio = audio[:1280]

    # Convert back to int16 PCM
    audio = np.clip(audio, -32768, 32767).astype(np.int16)

    return audio