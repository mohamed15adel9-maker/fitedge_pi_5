from recorder.recorder import record_audio
from speech.transcriber import transcribe
from tts.speaker import speak
from wakeword.detector import wait_for_wake_word
from cleaning_speech import clean_for_speech
from brain.agent import run_agent

from memory.manager import add_message

from display.oled_faces import (
    sleeping_face,
    smiling_face,
    listening_face,
    thinking_face,
    speaking_face,
)

CONVERSATION_ID = "default"

# Phrases that end the current conversation
DONE_PHRASES = [
    "bye",
    "goodbye",
    "stop",
    "exit",
    "quit",
    "thank you",
    "thanks",
    "i'm done",
    "im done",
    "that's all",
    "thats all",
    "nothing else",
]


def should_end(text):
    """
    Returns True if the user wants to end the conversation.
    """
    text = text.lower().strip()

    for phrase in DONE_PHRASES:
        if phrase in text:
            return True

    return False


def main():

    # Show sleeping face on startup
    sleeping_face()

    while True:

        # =====================================================
        # WAIT FOR WAKE WORD
        # =====================================================
        smiling_face()

        print("===================================")
        print("Waiting for wake word...")
        print("===================================")

        wait_for_wake_word()

        print("Wake word detected!")

        

        # =====================================================
        # CONVERSATION LOOP
        # =====================================================

        while True:

            # ---------------------------------------------
            # LISTEN
            # ---------------------------------------------

            listening_face()

            print("Recording...")

            recorded_audio = record_audio()

            # ---------------------------------------------
            # THINK
            # ---------------------------------------------

            thinking_face()

            print("Transcribing...")

            transcribed_text = transcribe(recorded_audio)

            print("User:", transcribed_text)

            if not transcribed_text:
                print("Nothing detected.")

                # Continue listening
                listening_face()
                continue

            transcribed_text = transcribed_text.strip()

            if transcribed_text == "":
                listening_face()
                continue

            # ---------------------------------------------
            # END CONVERSATION?
            # ---------------------------------------------

            if should_end(transcribed_text):

                speaking_face()

                goodbye = "Goodbye!"

                print("Assistant:", goodbye)

                speak(goodbye)

                sleeping_face()

                print("Conversation ended.\n")

                break

            # ---------------------------------------------
            # BUILD MESSAGE
            # ---------------------------------------------

            messages = [
                {
                    "role": "user",
                    "content": transcribed_text,
                }
            ]

            # Optional debug file
            try:
                with open(
                    "/tmp/fitedge_prompt.txt",
                    "w",
                    encoding="utf-8",
                ) as f:

                    f.write("========== USER REQUEST ==========\n")
                    f.write(transcribed_text)

            except Exception as e:
                print("Debug file error:", e)

            # ---------------------------------------------
            # AGENT
            # ---------------------------------------------

            thinking_face()

            print("Calling agent...")

            response = run_agent(messages, 1)

            print("Assistant:", response)

            # ---------------------------------------------
            # SAVE MEMORY
            # ---------------------------------------------

            speech = clean_for_speech(response)

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

            # ---------------------------------------------
            # SPEAK
            # ---------------------------------------------

            speaking_face()

            print("Speaking...")

            speak(speech)

            # Smile after speaking
            smiling_face()

            print("-----------------------------------")
            print("Listening for follow-up...")
            print("-----------------------------------")

        # Return to wake-word mode
        sleeping_face()

        print("Returning to wake-word mode...\n")


if __name__ == "__main__":
    main()