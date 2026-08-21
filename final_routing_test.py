from brain.llm import route_request


CASES = {
    # ============================================================
    # BASIC / SINGLE-DOMAIN
    # ============================================================

    "what are my current goals?": ["database"],
    "what's my weather like right now?": ["weather"],
    "what's the forecast for tomorrow morning?": ["weather"],
    "show me my upcoming calendar events": ["calendar"],
    "did I get any new emails?": ["email"],
    "what did I do for workouts recently?": ["fitness"],
    "what was my latest weight?": ["database"],
    "what injuries do you have on file for me?": ["database"],
    "what workouts have I done lately?": ["fitness"],
    "what was my last run?": ["fitness"],
    "what's my HRV this week?": ["fitness"],
    "tell me my profile details": ["database"],
    "remember that I like training in the morning": ["database"],
    "save that I prefer short workouts": ["database"],
    "start a push-up session": ["vision"],
    "watch me do some pushups": ["vision"],
    "scan this meal": ["vision"],
    "analyze what's on my plate": ["vision"],
    "goodbye": ["session"],
    "I'm finished": ["session"],

    # ============================================================
    # GENERAL / NO-TOOL QUESTIONS
    # ============================================================

    "what's a good source of protein?": ["none"],
    "how much protein is in an egg?": ["none"],
    "is training to failure always necessary?": ["none"],
    "what's the difference between hypertrophy and strength training?": ["none"],
    "how can I improve my push-up technique?": ["none"],
    "what should I eat after a workout?": ["none"],
    "is walking good for recovery?": ["none"],
    "how long should I rest between sets?": ["none"],
    "why do muscles get sore after training?": ["none"],
    "what is zone 2 cardio?": ["none"],

    # ============================================================
    # DATABASE + OTHER
    # ============================================================

    "what are my goals and what injuries do I have?": ["database"],
    "check my weight and tell me the weather": ["database", "weather"],
    "what are my goals and what's on my calendar tomorrow?": [
        "database", "calendar"
    ],
    "remember I prefer mornings, and also tell me my current goals": [
        "database"
    ],
    "what do you remember about me and what's the weather?": [
        "database", "weather"
    ],
    "check my profile and tell me when my next meeting is": [
        "database", "calendar"
    ],
    "what are my injuries and should I train today?": [
        "database", "fitness"
    ],
    "what are my goals and what workouts have I done recently?": [
        "database", "fitness"
    ],
    "remember that I like morning workouts and add that to my profile": [
        "database"
    ],
    "save my new preference and check tomorrow's calendar": [
        "database", "calendar"
    ],

    # ============================================================
    # WEATHER + CALENDAR
    # ============================================================

    "what's the weather tomorrow and am I free?": [
        "weather", "calendar"
    ],
    "is it going to rain during my run tomorrow, and what's on my calendar?": [
        "weather", "calendar"
    ],
    "if it's sunny tomorrow, put a run on my calendar": [
        "weather", "calendar"
    ],
    "schedule a workout tomorrow if the weather is good": [
        "weather", "calendar"
    ],
    "can I train outside tomorrow morning based on the forecast?": [
        "weather"
    ],
    "find a free time tomorrow when the weather is clear": [
        "weather", "calendar"
    ],
    "check whether it's raining before my evening workout": [
        "weather"
    ],
    "if it won't rain, schedule my run for tomorrow": [
        "weather", "calendar"
    ],

    # ============================================================
    # FITNESS + WEATHER
    # ============================================================

    "should I run outside tomorrow if it's hot?": [
        "weather", "fitness"
    ],
    "what was my last run and what will the weather be like tomorrow?": [
        "fitness", "weather"
    ],
    "compare my recent run with tomorrow's weather": [
        "fitness", "weather"
    ],
    "I want to run tomorrow; is the weather suitable and what did I do last time?": [
        "weather", "fitness"
    ],
    "is it cool enough tomorrow for the kind of training I've been doing?": [
        "weather", "fitness"
    ],
    "check my recent cardio and tell me whether tomorrow looks good for another run": [
        "fitness", "weather"
    ],

    # ============================================================
    # FITNESS + CALENDAR
    # ============================================================

    "what workout did I do last time and what do I have scheduled tomorrow?": [
        "fitness", "calendar"
    ],
    "check my recent training and my calendar for the weekend": [
        "fitness", "calendar"
    ],
    "what did I train yesterday, and am I free tonight?": [
        "fitness", "calendar"
    ],
    "look at my recent activities and tell me whether I have time to train tomorrow": [
        "fitness", "calendar"
    ],
    "what's my next workout and when is my next calendar event?": [
        "fitness", "calendar"
    ],

    # ============================================================
    # DATABASE + FITNESS + WEATHER
    # ============================================================

    "check my goals, recent workouts, and tomorrow's weather": [
        "database", "fitness", "weather"
    ],
    "what injuries do I have, what did I train recently, and will it rain tomorrow?": [
        "database", "fitness", "weather"
    ],
    "look at my current goals and recent cardio, then tell me if tomorrow is good for a run": [
        "database", "fitness", "weather"
    ],
    "what's my latest weight, what did I do yesterday, and what's the forecast?": [
        "database", "fitness", "weather"
    ],
    "check my profile, my recent workouts, and my calendar for tomorrow": [
        "database", "fitness", "calendar"
    ],
    "what are my goals, what have I trained lately, and am I free tomorrow?": [
        "database", "fitness", "calendar"
    ],

    # ============================================================
    # EMAIL COMBINATIONS
    # ============================================================

    "read my recent emails and check tomorrow's weather": [
        "email", "weather"
    ],
    "check my email and tell me what I have on the calendar today": [
        "email", "calendar"
    ],
    "read my emails, check my goals, and tell me tomorrow's forecast": [
        "email", "database", "weather"
    ],
    "draft an email about my workout and check my calendar": [
        "email", "fitness", "calendar"
    ],
    "send an email and then tell me the weather": [
        "email", "weather"
    ],
    "check my email before we start my push-up session": [
        "email", "vision"
    ],
    "draft an email saying I finished my workout": [
        "email", "fitness"
    ],
    "read my latest email and then start a push-up session": [
        "email", "vision"
    ],

    # ============================================================
    # VISION COMBINATIONS
    # ============================================================

    "check my goals then start a push-up session": [
        "database", "vision"
    ],
    "what did I do last workout, then watch me do pushups": [
        "fitness", "vision"
    ],
    "scan my food and tell me the weather": [
        "vision", "weather"
    ],
    "analyze my meal, then tell me what I have on my calendar": [
        "vision", "calendar"
    ],
    "check my injuries before starting a push-up session": [
        "database", "vision"
    ],
    "remember that I prefer mornings, then start my workout": [
        "database", "vision"
    ],
    "start a push-up session if the weather is good": [
        "vision", "weather"
    ],
    "check my goals and scan my food": [
        "database", "vision"
    ],

    # ============================================================
    # SESSION / EXIT COMBINATIONS
    # ============================================================

    "goodbye, that's all": ["session"],
    "I'm done, log me out": ["session"],
    "I need to stop using FitEdge": ["session"],
    "check my goals and then I'm done": ["database", "session"],
    "tell me the weather and then log me out": ["weather", "session"],
    "read my email and then end the session": ["email", "session"],
    "check my calendar before I sign out": ["calendar", "session"],
    "check my goals and then goodbye": ["database", "session"],

    # ============================================================
    # HARDER CONVERSATIONAL / IMPLICIT CASES
    # ============================================================

    "I think I trained yesterday; can you remind me what I did?": [
        "fitness"
    ],
    "Do you remember what I'm working toward these days?": [
        "database"
    ],
    "I'm heading out for a run tomorrow morning — should I worry about the weather?": [
        "weather"
    ],
    "I just finished training; what does that say about my recent activity history?": [
        "fitness"
    ],
    "I don't remember whether I'm free tomorrow afternoon — check for me": [
        "calendar"
    ],
    "I need to know whether I've received anything important": [
        "email"
    ],
    "can you keep in mind that I prefer morning sessions from now on?": [
        "database"
    ],
    "before I train, remind me what my current limitations are": [
        "database"
    ],
    "I'm about to do pushups; count them for me": [
        "vision"
    ],
    "here's my lunch, can you take a look at it?": [
        "vision"
    ],

    # ============================================================
    # MORE MIXED / EDGE CASES
    # ============================================================

    "what's my weight, what was my last workout, and is it going to rain tonight?": [
        "database", "fitness", "weather"
    ],
    "check tomorrow's forecast, my calendar, and my last cardio session": [
        "weather", "calendar", "fitness"
    ],
    "I want to schedule a run after checking the forecast and my existing events": [
        "weather", "calendar"
    ],
    "look at my goals and injuries before we train": [
        "database", "vision"
    ],
    "what are my recent workouts, my current weight, and my next appointment?": [
        "fitness", "database", "calendar"
    ],
    "I need to send something by email, but first check whether I'm free tomorrow": [
        "email", "calendar"
    ],
    "can you check my recent workout, the weather, and whether I have anything booked tonight?": [
        "fitness", "weather", "calendar"
    ],
    "I'm done for today, but tell me my last workout before you sign me out": [
        "fitness", "session"
    ],
    "scan my meal, check my goals, and tell me whether I have training tomorrow": [
        "vision", "database", "calendar"
    ],
    "I want to do pushups, but first check my injuries and whether the weather matters": [
        "database", "vision", "weather"
    ],
}


def main():
    passed = 0
    failed = 0

    print("=" * 80)
    print("FITEDGE ROUTER STRESS TEST")
    print(f"Total cases: {len(CASES)}")
    print("=" * 80)

    for i, (msg, expected) in enumerate(CASES.items(), 1):
        try:
            got = route_request(msg)

            ok = set(got) == set(expected)

            if ok:
                passed += 1
                mark = "✓"
            else:
                failed += 1
                mark = "✗"

            print(
                f"{mark} {i:02d}. "
                f"'{msg}'"
            )
            print(
                f"    got      = {got}"
            )
            print(
                f"    expected = {expected}"
            )

        except Exception as e:
            failed += 1

            print(
                f"✗ {i:02d}. "
                f"'{msg}'"
            )
            print(
                f"    ERROR: "
                f"{type(e).__name__}: {e}"
            )
            print(
                f"    expected = {expected}"
            )

    print()
    print("=" * 80)
    print("ROUTER STRESS TEST COMPLETE")
    print("=" * 80)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {len(CASES)}")

    if failed == 0:
        print("ALL ROUTER CASES PASSED ✓")
    else:
        print(
            f"{failed} ROUTER CASE(S) FAILED ✗"
        )


if __name__ == "__main__":
    main()
