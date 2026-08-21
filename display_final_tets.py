"""
test_fetch_display.py

End-to-end test for:

    FitEdge tool
        ↓
    executor.run_tool()
        ↓
    display_data / display_type
        ↓
    display.data.show_data()
        ↓
    OLED

Run from the FitEdge project root:

    python test_fetch_display.py
"""

from tools.executor import run_tool
from display.data import show_data


USER = 1


def run_display_test(tool_name, args, label):
    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    try:
        result = run_tool(
            tool_name,
            args,
            USER,
        )

        print("TOOL RESULT:")
        print(result)

        # ----------------------------------------------------
        # Display path
        # ----------------------------------------------------

        if not isinstance(result, dict):
            print("No display payload returned.")
            return

        display_data = result.get("display_data")
        display_type = result.get("display_type")

        print()
        print("DISPLAY TYPE:")
        print(display_type)

        print()
        print("DISPLAY DATA:")
        print(display_data)

        if display_data:
            print()
            print("Sending to OLED...")

            show_data(
                display_data,
                display_type,
            )

            print("OLED display call completed.")

        else:
            print("display_data is empty; nothing sent to OLED.")

    except Exception as e:
        print(
            f"ERROR: {type(e).__name__}: {e}"
        )


# ============================================================
# DATABASE
# ============================================================

run_display_test(
    "get_active_goals",
    {},
    "DISPLAY TEST: goals",
)

run_display_test(
    "get_latest_measurement",
    {},
    "DISPLAY TEST: measurement",
)

run_display_test(
    "get_active_injuries",
    {},
    "DISPLAY TEST: injuries",
)

run_display_test(
    "get_user_profile",
    {},
    "DISPLAY TEST: profile",
)


# ============================================================
# CALENDAR
# ============================================================

run_display_test(
    "get_calendar_events",
    {
        "days_ahead": 7,
        "max_results": 5,
    },
    "DISPLAY TEST: calendar",
)


# ============================================================
# WGER
# ============================================================

run_display_test(
    "get_recent_workouts",
    {
        "limit": 3,
    },
    "DISPLAY TEST: wger workouts",
)

run_display_test(
    "get_weight_log",
    {
        "limit": 3,
    },
    "DISPLAY TEST: wger weight log",
)


# ============================================================
# INTERVALS
# ============================================================

run_display_test(
    "get_recent_activities",
    {
        "days_back": 30,
        "limit": 3,
    },
    "DISPLAY TEST: Intervals activities",
)

run_display_test(
    "get_wellness",
    {
        "days_back": 7,
    },
    "DISPLAY TEST: Intervals wellness",
)


# ============================================================
# WEATHER
# ============================================================

run_display_test(
    "get_current_weather",
    {},
    "DISPLAY TEST: current weather",
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("FETCH + DISPLAY TEST COMPLETE")
print("=" * 70)