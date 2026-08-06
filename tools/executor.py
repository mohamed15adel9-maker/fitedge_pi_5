from memory.query import execute_query
from tools.calendar import get_calendar_events, add_calendar_event
from tools.weather import get_current_weather, get_hourly_weather, get_daily_weather
from tools.email import draft_email, send_email, read_recent_emails
from tools.wger import get_recent_workouts, get_weight_log, add_weight_entry
from tools.intervals import get_recent_activities, get_activity_details, get_wellness


def run_tool(name, args):
    if name == "execute_query":
        return execute_query(args.get("sql", ""))

    if name == "get_calendar_events":
        return get_calendar_events(days_ahead=args.get("days_ahead", 7),
                                   max_results=args.get("max_results", 10))
    if name == "add_calendar_event":
        return add_calendar_event(title=args.get("title", ""),
                                  date=args.get("date", ""),
                                  start_time=args.get("start_time", "09:00"),
                                  duration_minutes=args.get("duration_minutes", 60))

    if name == "draft_email":
        return draft_email(args.get("to",""), args.get("subject",""), args.get("body",""))
    if name == "send_email":
        return send_email(args.get("to",""), args.get("subject",""), args.get("body",""))
    if name == "read_recent_emails":
        return read_recent_emails(max_results=args.get("max_results", 5))

    if name == "get_recent_workouts":
        return get_recent_workouts(limit=args.get("limit", 5))
    if name == "get_weight_log":
        return get_weight_log(limit=args.get("limit", 5))
    if name == "add_weight_entry":
        return add_weight_entry(weight=args.get("weight"), entry_date=args.get("entry_date"))

    if name == "get_recent_activities":
        return get_recent_activities(days_back=args.get("days_back", 14),
                                     limit=args.get("limit", 10))
    if name == "get_wellness":
        return get_wellness(days_back=args.get("days_back", 7))

    if name == "get_current_weather":
        return str(get_current_weather(latitude=args.get("latitude"), longitude=args.get("longitude")))
    if name == "get_hourly_weather":
        return str(get_hourly_weather(latitude=args.get("latitude"), longitude=args.get("longitude"), hours=args.get("hours", 24)))
    if name == "get_daily_weather":
        return str(get_daily_weather(latitude=args.get("latitude"), longitude=args.get("longitude"), days=args.get("days", 7)))

    if name == "get_activity_details":
        return get_activity_details(args.get("activity_id"))
    return f"Unknown tool: {name}"