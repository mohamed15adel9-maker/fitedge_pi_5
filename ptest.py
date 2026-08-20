from vision.push_up import run_pushup_session


def main():

    print()
    print("========================================")
    print(" PUSH-UP INTEGRATION TEST")
    print("========================================")
    print()
    print("Test sequence:")
    print("1. Stand normally for a few seconds.")
    print("2. Get into your push-up starting position.")
    print("3. Hold the position until the session starts.")
    print("4. Do 3-5 push-ups.")
    print("5. Stand up.")
    print("6. The session should automatically end.")
    print()
    print("Press Q in the camera window to stop.")
    print()

    result = run_pushup_session()

    print()
    print("========================================")
    print(" SESSION RESULT")
    print("========================================")
    print()
    print(f"Correct reps:   {result['correct_reps']}")
    print(f"Incorrect reps: {result['incorrect_reps']}")
    print(f"Total reps:     {result['total_reps']}")
    print(f"Feedback:       {result['feedback']}")
    print()


if __name__ == "__main__":
    main()