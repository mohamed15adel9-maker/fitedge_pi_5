from openwakeword.model import Model
from microphone_chunk import get_microphone_chunk
from microphone_chunk import start_microphone, stop_microphone
print("Loading wake word model...")

model = Model(wakeword_models=["alexa"], inference_framework="onnx")

def wait_for_wake_word():
    start_microphone()
    print("Waiting for wake word...")
    
    while True:
        
        audio_chunk = get_microphone_chunk()
        predictions = model.predict(audio_chunk)


        print(predictions)
        if(predictions["alexa"] >0.5):
            print("wake word detected")

            stop_microphone()
            return
