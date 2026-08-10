from openwakeword.model import Model
from microphone_chunk import (
    get_microphone_chunk,
    start_microphone,
    stop_microphone
)

import numpy as np
import soundfile as sf

print("Loading wake word model...")

model = Model(
    wakeword_model_paths=[
        "/home/mo/FitEdge/venv/lib/python3.13/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
    ]
)

def wait_for_wake_word():
    start_microphone()
    print("Waiting for wake word...")

    debug_audio = []      # <-- add this

    while True:

        audio_chunk = get_microphone_chunk()

        print(audio_chunk.shape)
        print(audio_chunk.dtype)

        debug_audio.append(audio_chunk.copy())

        # Save about 10 seconds
        if len(debug_audio) == 125:
            full = np.concatenate(debug_audio)
            sf.write("debug.wav", full, 16000)
            print("Saved debug.wav")
            debug_audio = []

        audio_chunk = audio_chunk * 0.1
        predictions = model.predict(audio_chunk)

        print(predictions)

        if predictions["hey_jarvis_v0.1"] > 0.5:
          print("Wake word detected")
          stop_microphone()
          return