from recorder.recorder import record_audio
from speech.transcriber import transcribe
from tts.speaker import speak
from wakeword.detector import wait_for_wake_word
from cleaning_speech import clean_for_speech
from brain.agent import run_agent
from difflib import SequenceMatcher
from memory.manager import get_all_users, add_message
import time
from memory.manager import add_message


CONVERSATION_ID = "default"

DONE_PHRASES = ["i'm done", "i am done", "that's all", "log me out",
                "goodbye", "sign me out", "im done"]

SESSION_TIMEOUT = 300   # 5 minutes of inactivity -> auto logout


def lookup_user_by_name(spoken_name):
    """Fuzzy-match the spoken name to a user. Returns user_id or None."""
    spoken = spoken_name.lower().strip()
    best, best_score = None, 0
    for user in get_all_users():
        score = SequenceMatcher(None, spoken, user["name"].lower()).ratio()
        if score > best_score:
            best, best_score = user, score
    return best["id"] if best_score >= 0.6 else None


def is_done_phrase(text):
    low = text.lower().strip()
    return any(low == p or low.startswith(p) for p in DONE_PHRASES)


def main():

    while True:
        current_user_id = None
        last_active = time.time()

        # -----------------------------------------------------
        # 1. WAIT FOR WAKE WORD
        # -----------------------------------------------------

        print("1. Waiting for wake word...")
        wait_for_wake_word()

        if current_user_id is not None and (time.time() - last_active) > SESSION_TIMEOUT:
            print("Session timed out.")
            current_user_id = None

        # --- no one logged in: ask for the name ---
        if current_user_id is None:
            speak("Who am I speaking with?")
            print("introduce yourself")
            audio = record_audio()
            name = transcribe(audio).strip()
            if not name:
                speak("I didn't catch that.")
                continue
            uid = lookup_user_by_name(name)
            if uid is None:
                speak(f"I don't recognize {name}. Please try again.")
                continue
            current_user_id = uid
            last_active = time.time()
            # get their name back for the greeting
            speak("Hi! How can I help?")
            continue

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

        if is_done_phrase(text):
            speak("Goodbye!")
            current_user_id = None
            continue

        transcribed_text = transcribed_text.strip()

        last_active = time.time()

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
            messages,1
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
