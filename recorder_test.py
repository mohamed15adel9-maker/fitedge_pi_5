from recorder.recorder import record_audio
from speech.transcriber import transcribe

audio = record_audio()          # speak while it records
text = transcribe(audio)
print("You said:", text)