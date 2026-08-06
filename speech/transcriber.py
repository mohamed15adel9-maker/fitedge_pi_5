from pathlib import Path
import subprocess
import re

# Project root
ROOT = Path(__file__).resolve().parent.parent

WHISPER = (
    ROOT
    / "whisper.cpp"
    / "build"
    / "bin"
    / "Release"
    / "whisper-cli.exe"
)

MODEL = (
    ROOT
    / "whisper.cpp"
    / "models"
    / "ggml-base.en.bin"
)


def transcribe(audio_path):

    result = subprocess.run(
        [
            str(WHISPER),
            "-m",
            str(MODEL),
            "-f",
            str(audio_path),
            "-l",
            "en",
            "--no-timestamps",
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    output = result.stdout.strip()

    # Remove empty lines
    lines = [line.strip() for line in output.splitlines() if line.strip()]

    # Return the last spoken sentence
    return lines[-1] if lines else ""