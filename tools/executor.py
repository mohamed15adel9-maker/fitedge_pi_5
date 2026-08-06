from memory.query import execute_query
from tools.calendar import get_calendar_events, add_calendar_event


def run_tool(name, args):
    if name == "execute_query":
        return execute_query(args.get("sql", ""))

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

    return f"Unknown tool: {name}"