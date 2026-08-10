import sounddevice as sd
import numpy as np
from scipy.signal import resample_poly
from openwakeword.model import Model

# Load the built-in Jarvis wake-word model
model = Model(
    wakeword_model_paths=[
        "/home/mo/FitEdge/venv/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
    ]
)

# Audio settings
SAMPLE_RATE = 44100
CHUNK_SIZE = 3528  # 80 ms at 44.1 kHz

# Open microphone
stream = sd.InputStream(
    device=1,          # USB microphone
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype=np.int16,
)

stream.start()

print("Say 'Hey Jarvis'...")

while True:
    # Read 80 ms of audio
    chunk, overflowed = stream.read(CHUNK_SIZE)

    # Convert to 1D array
    audio = chunk.flatten()

    # Resample from 44.1 kHz to 16 kHz
    audio = resample_poly(audio, up=160, down=441)

    # Ensure exactly 1280 samples
    audio = audio[:1280]

    # Convert back to int16 PCM
    audio = np.clip(audio, -32768, 32767).astype(np.int16)

    # Predict
    prediction = model.predict(audio)

    # Print confidence
    print(prediction["hey_jarvis_v0.1"])