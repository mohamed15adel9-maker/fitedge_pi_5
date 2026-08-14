"""
tools/executor.py

Executes one FitEdge tool by name. This is the single translation layer:
    LLM tool name  ->  the real function (with user_id injected for DB tools)

Single-user system: all database operations use USER_ID.
"""

# =========================================================
# DATABASE  (your own memory/manager.py — no wrapper)
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
from tools.weather import get_current_weather, get_hourly_weather, get_daily_weather
from tools.email import draft_email, send_email, read_recent_emails

# =========================================================
# WGER / INTERVALS
# =========================================================
from tools.wger import get_recent_workouts, get_weight_log, add_weight_entry
from tools.intervals import get_recent_activities, get_activity_details, get_wellness

# Single-user system.
USER_ID = 1


def run_tool(name, args):
    """Execute one FitEdge tool and return its result."""

    # =====================================================
    # DATABASE — READ  (user_id injected here)
    # =====================================================
    if name == "get_active_goals":
        return get_active_goals(USER_ID)
    if name == "get_latest_measurement":
        return get_latest_measurement(USER_ID)
    if name == "get_active_injuries":
        return get_active_injuries(USER_ID)
    if name == "get_recent_workouts_db":
        return get_workouts(USER_ID, limit=args.get("limit", 5))
    if name == "get_user_fact":
        return get_fact(USER_ID, args.get("key", ""))
    if name == "get_user_profile":
        return get_user(USER_ID)

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
        return {"success": True, "user_id": user_id,
                "message": "User profile created successfully."}

    if name == "create_goal":
        goal_id = db_create_goal(
            user_id=USER_ID,
            title=args.get("title"),
            description=args.get("description"),
            priority=args.get("priority"),
            status="active",
            start_date=args.get("start_date"),
            target_date=args.get("target_date"),
        )
        return {"success": True, "goal_id": goal_id,
                "message": "Fitness goal created successfully."}

    if name == "create_measurement":
        measurement_id = db_create_measurement(
            user_id=USER_ID,
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
        return {"success": True, "measurement_id": measurement_id,
                "message": "Measurement saved successfully."}

    if name == "create_injury":
        injury_id = db_create_injury(
            user_id=USER_ID,
            body_part=args.get("body_part"),
            description=args.get("description"),
            severity=args.get("severity"),
            date=args.get("date"),
            active=args.get("active", True),
        )
        return {"success": True, "injury_id": injury_id,
                "message": "Injury recorded successfully."}

    if name == "create_fact":
        fact_id = db_create_fact(
            user_id=USER_ID,
            key=args.get("key"),
            value=args.get("value"),
            confidence=args.get("confidence", 1.0),
        )
        return {"success": True, "fact_id": fact_id,
                "message": "Fact stored successfully."}

    # =====================================================
    # CALENDAR
    # =====================================================
    if name == "get_calendar_events":
        return get_calendar_events(
            days_ahead=args.get("days_ahead", 7),
            max_results=args.get("max_results", 10),
        )
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
        return draft_email(args.get("to", ""), args.get("subject", ""), args.get("body", ""))
    if name == "send_email":
        return send_email(args.get("to", ""), args.get("subject", ""), args.get("body", ""))
    if name == "read_recent_emails":
        return read_recent_emails(max_results=args.get("max_results", 5))

    # =====================================================
    # WGER / STRENGTH
    # =====================================================
    if name == "get_recent_workouts":
        return get_recent_workouts(limit=args.get("limit", 5))
    if name == "get_weight_log":
        return get_weight_log(limit=args.get("limit", 5))
    if name == "add_weight_entry":
        return add_weight_entry(
            weight=args.get("weight"),
            entry_date=args.get("entry_date"),
        )

    # =====================================================
    # CARDIO / RECOVERY (Intervals.icu)
    # =====================================================
    if name == "get_recent_activities":
        return get_recent_activities(
            days_back=args.get("days_back", 14),
            limit=args.get("limit", 10),
        )
    if name == "get_wellness":
        return get_wellness(days_back=args.get("days_back", 7))
    if name == "get_activity_details":
        return get_activity_details(args.get("activity_id"))

    # =====================================================
    # WEATHER
    # =====================================================
    if name == "get_current_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9
        
        return str(get_current_weather(
            lat,
            lon,
        ))
    if name == "get_hourly_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9
                
        return str(get_hourly_weather(
            latitude=lat,
            longitude=lon,
            hours=args.get("hours", 24),
        ))
    if name == "get_daily_weather":
        lat = args.get("latitude") or 31.2
        lon = args.get("longitude") or 29.9
                
        return str(get_daily_weather(
            latitude=lat,
            longitude=lon,
            days=args.get("days", 7),
        ))

    # =====================================================
    # UNKNOWN
    # =====================================================
    return f"Unknown tool: {name}"
