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
        wait_for_wake_word()

        recorded_audio = record_audio()
        transcribed_text = transcribe(recorded_audio)
        print("Transcribed text:", transcribed_text)

        if not transcribed_text or not transcribed_text.strip():
            continue

        # save the user message so conversation memory accumulates
        add_message(CONVERSATION_ID, "user", transcribed_text)

        # build_prompt already includes the system prompt + context + message
        messages = [
            {"role": "user", "content": build_prompt(transcribed_text)},
        ]

        # run the agent loop (tool-calling happens inside)
        response = run_agent(messages)

        # save the reply
        add_message(CONVERSATION_ID, "assistant", response)

        speak(response)


if __name__ == "__main__":
    main()