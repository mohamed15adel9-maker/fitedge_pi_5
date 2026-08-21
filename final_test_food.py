"""
test_food_live.py

Tests the live FitEdge food-recognition pipeline.

Test flow:
    1. Load the food model.
    2. Open the webcam.
    3. Capture frames continuously.
    4. Run live food classification.
    5. Display the current classifications.
    6. Press Q to end the session.
"""

from vision.food import analyze_food_image


def main():
    print("=" * 70)
    print("FITEDGE LIVE FOOD RECOGNITION TEST")
    print("=" * 70)

    print()
    print("Instructions:")
    print("1. Make sure the webcam is connected.")
    print("2. Put a plate/food in front of the camera.")
    print("3. Move the plate around if necessary.")
    print("4. Watch the live classification window.")
    print("5. Press Q to finish.")
    print()

    try:
        result = analyze_food_image()

        print()
        print("=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        print(result)

    except KeyboardInterrupt:
        print()
        print("Test interrupted by user.")

    except Exception as e:
        print()
        print("=" * 70)
        print("TEST ERROR")
        print("=" * 70)
        print(
            f"{type(e).__name__}: {e}"
        )


if __name__ == "__main__":
    main()