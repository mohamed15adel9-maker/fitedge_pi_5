import whisper

print("Loading Whisper model...")
model = whisper.load_model("base")


def transcribe(audio_path):
    print("Transcribing...")

    result = model.transcribe(
        audio_path,
        language="en",
        fp16=False
    )

    text = result["text"].strip()

    print("You said:", text)

    return text