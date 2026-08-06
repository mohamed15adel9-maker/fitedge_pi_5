import sounddevice as sd
import numpy as np

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280

stream = None

def start_microphone():
    global stream

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype=np.int16
    )

    stream.start()


def stop_microphone():
    global stream

    if stream is not None:
        stream.stop()
        stream.close()
        stream = None


def get_microphone_chunk():
    chunk, overflowed = stream.read(CHUNK_SIZE)
    return chunk.flatten()