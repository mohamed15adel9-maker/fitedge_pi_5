from wakeword.detector import wait_for_wake_word
from recorder.recorder import record_audio
from speech.transcriber import transcribe
from tts.speaker import speak

wait_for_wake_word()
audio = record_audio()
text = transcribe(audio)
print("Heard:", text)
speak("You said: " + text)