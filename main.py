from recorder.recorder import record_audio
from speech.transcriber import transcribe
from tts.speaker import speak
from wakeword.detector import wait_for_wake_word
from cleaning_speech import clean_for_speech
from brain.agent import run_agent

from memory.manager import add_message


CONVERSATION_ID = "default"


def main():

    while True:

        # -----------------------------------------------------
        # 1. WAIT FOR WAKE WORD
        # -----------------------------------------------------

        print("1. Waiting for wake word...")
        wait_for_wake_word()

        # -----------------------------------------------------
        # 2. RECORD AUDIO
        # -----------------------------------------------------

        print("2. Recording...")
        recorded_audio = record_audio()

        # -----------------------------------------------------
        # 3. TRANSCRIBE
        # -----------------------------------------------------

        print("3. Transcribing...")

        transcribed_text = transcribe(
            recorded_audio
        )

        print(
            "Transcribed text:",
            transcribed_text,
        )

        if not transcribed_text or not transcribed_text.strip():
            continue

        transcribed_text = transcribed_text.strip()

        # -----------------------------------------------------
        # 4. BUILD MINIMAL MESSAGE
        #
        # IMPORTANT:
        #
        # Do NOT build RAG/context here.
        #
        # The agent must first let Qwen:
        #
        #     user request
        #          ↓
        #       router
        #          ↓
        #     tool selection
        #
        # Only AFTER the tool executes will agent.py build:
        #
        #     RAG
        #     user facts
        #     conversation history
        #     tool result
        #
        # This keeps the Qwen tool-selection prompt small.
        # -----------------------------------------------------

        print("4. Building messages...")

        messages = [
            {
                "role": "user",
                "content": transcribed_text,
            }
        ]

        print(
            "Number of messages:",
            len(messages),
        )

        print(
            "User message:",
            transcribed_text,
        )

        # -----------------------------------------------------
        # DEBUG USER REQUEST
        # -----------------------------------------------------

        try:

            with open(
                "/tmp/fitedge_prompt.txt",
                "w",
                encoding="utf-8",
            ) as f:

                f.write(
                    "========== USER REQUEST ==========\n"
                )

                f.write(
                    transcribed_text
                )

        except Exception as e:

            print(
                "Warning: Could not write debug prompt:",
                e,
            )

        print("Messages built.")

        # -----------------------------------------------------
        # 5. CALL AGENT
        #
        # The agent now handles:
        #
        #     Router
        #       ↓
        #     Tool selection
        #       ↓
        #     Tool execution
        #       ↓
        #     RAG + facts + history
        #       ↓
        #     Final Qwen answer
        # -----------------------------------------------------

        print("5. Calling agent...")

        response = run_agent(
            messages
        )

        print("Agent finished.")

        # -----------------------------------------------------
        # 6. SAVE CONVERSATION
        #
        # Save AFTER the agent finishes.
        #
        # This is intentional:
        # build_context() inside agent.py will not see the
        # current user message as old conversation history.
        # -----------------------------------------------------

        speech = clean_for_speech(response)
        print("6. Saving conversation...")

        add_message(
            CONVERSATION_ID,
            "user",
            transcribed_text,
        )

        add_message(
            CONVERSATION_ID,
            "assistant",
            response,
        )

        # -----------------------------------------------------
        # 7. SPEAK RESPONSE
        # -----------------------------------------------------
        

        print("7. Speaking...")

        speak(
            speech
        )

        print("Done.")
        print()


if __name__ == "__main__":
    main()
