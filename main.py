from recorder.recorder import record_audio
from tts.speaker import speak
from wakeword.detector import wait_for_wake_word
from cleaning_speech import clean_for_speech
from brain.agent import run_agent
from difflib import SequenceMatcher
from memory.manager import get_all_users, add_message, create_user
import time

from display.oled_faces import (
    sleeping_face,
    smiling_face,
    listening_face,
    thinking_face,
    speaking_face,
)

# Show sleeping face immediately on startup
sleeping_face()

# Import Whisper only after the OLED has updated
from speech.transcriber import load_model, transcribe

# Load the Whisper model while the sleeping face is displayed
load_model()
CONVERSATION_ID = "default"

DONE_PHRASES = ["i'm done.", "i am done.", "that's all.", "log me out.",
                "goodbye.", "sign me out.", "im done."]

SESSION_TIMEOUT = 900   # 5 minutes of inactivity -> auto logout


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
    sleeping_face()
    current_user_id = None
    last_active = time.time()

    # -------------------------
    # Helper functions
    # -------------------------

    def ask_text(question):
        """Ask until a non-empty response is received."""
        while True:
            speaking_face()
            speak(question)
            print(question)
            listening_face()
            audio = record_audio()
            thinking_face()
            text = transcribe(audio).strip()

            if text:
                return text
            speaking_face()
            speak("I didn't catch that. Please try again.")

    def ask_int(question):
        """Ask until a valid integer is received."""
        while True:
            text = ask_text(question)

            try:
                return int(text)
            except ValueError:
                speaking_face()
                speak("Please say a whole number.")

    def ask_float(question):
        """Ask until a valid number is received."""
        while True:
            text = ask_text(question)

            try:
                return float(text)
            except ValueError:
                speaking_face()
                speak("Please say a number.")

    def ask_sex():
        """Ask until Male or Female is received."""
        while True:
            speaking_face()
            text = ask_text("What is your sex? Male or Female?").lower()

            if text.startswith("m"):
                return "Male"

            if text.startswith("f"):
                return "Female"

            speak("Please say Male or Female.")

    while True:

        # -----------------------------------------------------
        # 1. WAIT FOR WAKE WORD
        # -----------------------------------------------------
        smiling_face()
        print("1. Waiting for wake word...")
        wait_for_wake_word()

        if current_user_id is not None and (time.time() - last_active) > SESSION_TIMEOUT:
            print("Session timed out.")
            current_user_id = None

        # -----------------------------------------------------
        # LOGIN / CREATE USER
        # -----------------------------------------------------

        if current_user_id is None:

            name = ask_text("Who am I speaking with?")

            uid = lookup_user_by_name(name)

            if uid is not None:
                current_user_id = uid
                last_active = time.time()
                speaking_face()
                speak(f"Welcome back {name}. How can I help?")
                continue
            speaking_face()
            speak(f"Nice to meet you, {name}. I need to create your profile.")

            age = ask_int("How old are you?")
            sex = ask_sex()
            height = ask_float("What is your height in centimeters?")

            current_user_id = create_user(
                name=name,
                age=age,
                sex=sex,
                height=height,
            )

            last_active = time.time()
            speaking_face()
            speak(
                f"Your profile has been created successfully, {name}. How can I help?"
            )
            continue

        # -----------------------------------------------------
        # 2. RECORD AUDIO
        # -----------------------------------------------------
        
        print("2. Recording...")
        listening_face()
        recorded_audio = record_audio()
        # -----------------------------------------------------
        # 3. TRANSCRIBE
        # -----------------------------------------------------
        thinking_face()
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
        

        if is_done_phrase(transcribed_text):
            speaking_face()
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
        thinking_face()
        response = run_agent(
            messages,current_user_id
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

        print(speech)

        add_message(
            CONVERSATION_ID,
            "user",
            transcribed_text,current_user_id
        )

        add_message(
            CONVERSATION_ID,
            "assistant",
            response,current_user_id
        )

        # -----------------------------------------------------
        # 7. SPEAK RESPONSE
        # -----------------------------------------------------
        

        print("7. Speaking...")
        speaking_face()
        speak(
            speech
        )
        smiling_face()
        print("Done.")
        print()


if __name__ == "__main__":
    sleeping_face()
    main()