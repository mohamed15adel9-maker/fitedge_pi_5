from recorder.recorder import record_audio
from speech.transcriber import transcribe
from tts.speaker import speak
from wakeword.detector import wait_for_wake_word
from brain.agent import run_agent
from build_context import build_prompt
from memory.manager import add_message

CONVERSATION_ID = "default"


def main():
    while True:
        print("1. Waiting for wake word...")
        wait_for_wake_word()

        print("2. Recording...")
        recorded_audio = record_audio()

        print("3. Transcribing...")
        transcribed_text = transcribe(recorded_audio)
        print("Transcribed text:", transcribed_text)

        if not transcribed_text or not transcribed_text.strip():
            continue

        print("4. Saving user message...")
        add_message(CONVERSATION_ID, "user", transcribed_text)

        print("5. Building prompt...")
        prompt = build_prompt(transcribed_text)
        with open("/tmp/fitedge_prompt.txt", "w", encoding="utf-8") as f:f.write(prompt)
        print("Prompt length:", len(prompt))
        print("Prompt preview:")
        print(prompt[:3000])
        print("END PROMPT PREVIEW")
        print("Prompt built.")

        messages = [
            {"role": "user", "content": prompt},
        ]

        print("6. Calling agent...")
        response = run_agent(messages)
        print("Agent finished.")

        print("7. Saving assistant message...")
        add_message(CONVERSATION_ID, "assistant", response)

        print("8. Speaking...")
        speak(response)

        print("Done.")


if __name__ == "__main__":
    main()