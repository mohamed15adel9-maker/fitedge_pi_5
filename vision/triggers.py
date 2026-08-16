"""
vision/triggers.py

Option B: detect when the user's spoken words are asking to scan food.
This is what makes a voice keyword directly trigger the camera.
"""

# Phrases that mean "look at my food". Add more as you like.
FOOD_TRIGGERS = [
    "scan my food",
    "scan my meal",
    "scan my plate",
    "check my food",
    "check my plate",
    "check my meal",
    "what am i eating",
    "what's on my plate",
    "whats on my plate",
    "analyze my food",
    "analyse my food",
    "log my meal",
    "log my food",
    "look at my food",
    "look at my plate",
]




def is_food_scan_request(text):
    """
    Returns True if the transcribed speech is asking to scan/see food.
    Case-insensitive substring match, so extra words around the phrase
    (e.g. "hey, can you scan my food please") still trigger.
    """
    if not text:
        return False
    low = text.lower()
    return any(trigger in low for trigger in FOOD_TRIGGERS)


EXERCISE_TRIGGERS = ["check my form", "what exercise", "am i doing this right", "check my squat"]

def is_exercise_request(text):
    low = text.lower()
    return any(t in low for t in EXERCISE_TRIGGERS)