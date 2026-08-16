import whisper

model = None

def load_model():
    global model

    if model is None:
        print("Loading Whisper model...")
        model = whisper.load_model("base")


def transcribe(audio_path):
    load_model()

    print("Transcribing...")

    result = model.transcribe(
        audio_path,
        language="en",
        fp16=False
    )

    text = result["text"].strip()

    print("You said:", text)

    return text