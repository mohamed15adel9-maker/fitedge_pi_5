"""
tools/executor.py

Executes one FitEdge tool by name. This is the single translation layer:
    LLM tool name  ->  the real function (with user_id injected for DB tools)

Single-user system: all database operations use USER_ID.
"""

# =========================================================
# DATABASE
# =========================================================
from memory.manager import (
    # reads
    get_active_goals,
    get_latest_measurement,
    get_active_injuries,
    get_workouts,
    get_fact,
    get_user,

    # writes
    create_user as db_create_user,
    create_goal as db_create_goal,
    create_measurement as db_create_measurement,
    create_injury as db_create_injury,
    create_fact as db_create_fact,
)

# =========================================================
# CALENDAR / WEATHER / EMAIL
# =========================================================
from tools.calendar import get_calendar_events, add_calendar_event

from tools.weather import (
    get_current_weather,
    get_hourly_weather,
    get_daily_weather,
)

from tools.email import (
    draft_email,
    send_email,
    read_recent_emails,
)

# =========================================================
# WGER / INTERVALS
# =========================================================
from tools.wger import (
    get_recent_workouts,
    get_weight_log,
    add_weight_entry,
)

from tools.intervals import (
    get_recent_activities,
    get_activity_details,
    get_wellness,
)

# =========================================================
# VISION
# =========================================================
from vision.push_up import run_pushup_session
from vision.food import analyze_food_image


# Single-user system.
USER_ID = 1


def run_tool(name, args, user_ID):
    """Execute one FitEdge tool and return its result."""

    # =====================================================
    # DATABASE — READ
    # =====================================================

    if name == "get_active_goals":
        return {
            "result": get_active_goals(user_ID),
            "display_data": True,
            "display_type": "goals",
        }

    if name == "get_latest_measurement":
        return {
            "result": get_latest_measurement(user_ID),
            "display_data": True,
            "display_type": "measurement",
        }

    if name == "get_active_injuries":
        return {
            "result": get_active_injuries(user_ID),
            "display_data": True,
            "display_type": "injuries",
        }

    if name == "get_recent_workouts_db":
        return {
            "result": get_workouts(
                user_ID,
                limit=args.get("limit", 5),
            ),
            "display_data": True,
            "display_type": "workouts",
        }

    if name == "get_user_fact":
        return {
            "result": get_fact(
                user_ID,
                args.get("key", ""),
            ),
            "display_data": True,
            "display_type": "fact",
        }

    if name == "get_user_profile":
        return {
            "result": get_user(user_ID),
            "display_data": True,
            "display_type": "profile",
        }

    # =====================================================
    # DATABASE — WRITE
    # =====================================================

    if name == "create_user":
        user_id = db_create_user(
            name=args.get("name"),
            age=args.get("age"),
            sex=args.get("sex"),
            height=args.get("height"),
        )

        return {
            "success": True,
            "user_id": user_id,
            "message": "User profile created successfully.",
        }

    if name == "create_goal":
        goal_id = db_create_goal(
            user_id=user_ID,
            title=args.get("title"),
            description=args.get("description"),
            priority=args.get("priority"),
            status="active",
            start_date=args.get("start_date"),
            target_date=args.get("target_date"),
        )

        return {
            "success": True,
            "goal_id": goal_id,
            "message": "Fitness goal created successfully.",
        }

    if name == "create_measurement":
        measurement_id = db_create_measurement(
            user_id=user_ID,
            date=args.get("date"),
            weight=args.get("weight"),
            body_fat=args.get("body_fat"),
            waist=args.get("waist"),
            chest=args.get("chest"),
            hips=args.get("hips"),
            left_arm=args.get("left_arm"),
            right_arm=args.get("right_arm"),
            left_thigh=args.get("left_thigh"),
            right_thigh=args.get("right_thigh"),
            left_calf=args.get("left_calf"),
            right_calf=args.get("right_calf"),
            neck=args.get("neck"),
            resting_heart_rate=args.get("resting_heart_rate"),
            notes=args.get("notes"),
        )

        return {
            "success": True,
            "measurement_id": measurement_id,
            "message": "Measurement saved successfully.",
        }

    if name == "create_injury":
        injury_id = db_create_injury(
            user_id=user_ID,
            body_part=args.get("body_part"),
            description=args.get("description"),
            severity=args.get("severity"),
            date=args.get("date"),
            active=args.get("active", True),
        )

        return {
            "success": True,
            "injury_id": injury_id,
            "message": "Injury recorded successfully.",
        }

    if name == "create_fact":
        fact_id = db_create_fact(
            user_id=user_ID,
            key=args.get("key"),
            value=args.get("value"),
            confidence=args.get("confidence", 1.0),
        )

        return {
            "success": True,
            "fact_id": fact_id,
            "message": "Fact stored successfully.",
        }

    # =====================================================
    # CALENDAR
    # =====================================================

    if name == "get_calendar_events":
        return {
            "result": get_calendar_events(
                days_ahead=args.get("days_ahead", 7),
                max_results=args.get("max_results", 10),
            ),
            "display_data": True,
            "display_type": "calendar",
        }

    if name == "add_calendar_event":
        return add_calendar_event(
            title=args.get("title", ""),
            date=args.get("date", ""),
            start_time=args.get("start_time", "09:00"),
            duration_minutes=args.get("duration_minutes", 60),
        )

    # =====================================================
    # EMAIL
    # =====================================================

    if name == "draft_email":
        return draft_email(
            args.get("to", ""),
            args.get("subject", ""),
            args.get("body", ""),
        )

    if name == "send_email":
        return send_email(
            args.get("to", ""),
            args.get("subject", ""),
            args.get("body", ""),
        )

    if name == "read_recent_emails":
        return read_recent_emails(
            max_results=args.get("max_results", 5),
        )

    # =====================================================
    # WGER / STRENGTH
    # =====================================================

    if name == "get_recent_workouts":
        return {
            "result": get_recent_workouts(
                limit=args.get("limit", 5),
            ),
            "display_data": True,
            "display_type": "workouts",
        }

    if name == "get_weight_log":
        return {
            "result": get_weight_log(
                limit=args.get("limit", 5),
            ),
            "display_data": True,
            "display_type": "weight_log",
        }

    if name == "add_weight_entry":
        return add_weight_entry(
            weight=args.get("weight"),
            entry_date=args.get("entry_date"),
        )

    # =====================================================
    # CARDIO / RECOVERY — Intervals.icu
    # =====================================================

    if name == "get_recent_activities":
        return {
            "result": get_recent_activities(
                days_back=14,
                limit=args.get("limit", 10),
            ),
            "display_data": True,
            "display_type": "activities",
        }

    if name == "get_wellness":
        return {
            "result": get_wellness(
                days_back=args.get("days_back", 7),
            ),
            "display_data": True,
            "display_type": "wellness",
        }

    if name == "get_activity_details":
        return {
            "result": get_activity_details(
                args.get("activity_id"),
            ),
            "display_data": True,
            "display_type": "activities",
        }

    # =====================================================
    # WEATHER
    # =====================================================

    if name == "get_current_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9

        return {
            "result": get_current_weather(
                lat,
                lon,
            ),
            "display_data": True,
            "display_type": "weather",
        }

    if name == "get_hourly_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9

        return {
            "result": get_hourly_weather(
                latitude=lat,
                longitude=lon,
                hours=args.get("hours", 24),
            ),
            "display_data": True,
            "display_type": "weather",
        }

    if name == "get_daily_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9

        return {
            "result": get_daily_weather(
                latitude=lat,
                longitude=lon,
                days=args.get("days", 7),
            ),
            "display_data": True,
            "display_type": "weather",
        }

    # =====================================================
    # END SESSION
    # =====================================================

    if name == "end_session":
        return "end_session"

    # =====================================================
    # VISION
    # =====================================================

    if name == "run_pushup_session":
        return str(
            run_pushup_session(
                target_reps=args.get("target_reps"),
            )
        )

    if name == "analyze_food_image":
        return str(
            analyze_food_image()
        )

    # =====================================================
    # UNKNOWN TOOL
    # =====================================================

    return f"Unknown tool: {name}"