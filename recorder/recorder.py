import sounddevice as sd
import soundfile as sf


def record_audio(filename="audio/recording.wav", duration=5, samplerate=16000):
    print("Recording... Speak now!")

    audio = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype="float32"
    )

    sd.wait()

    sf.write(filename, audio, samplerate)

    print(f"Saved recording to {filename}")

    return filename