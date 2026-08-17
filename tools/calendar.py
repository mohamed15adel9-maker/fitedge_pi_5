

from datetime import datetime, timedelta

from auth.google_auth import get_calendar_service


def get_calendar_events(days_ahead=7, max_results=10):
    
    try:
        service = get_calendar_service()

        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        result = service.events().list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = result.get("items", [])
        if not events:
            return "No upcoming events found."

        lines = []
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            summary = event.get("summary", "(no title)")
            lines.append(f"{start} - {summary}")

        return "\n".join(lines)

    except Exception as e:
        return f"ERROR reading calendar: {e}"


def add_calendar_event(title, date, start_time="09:00", duration_minutes=60):
    
    try:
        service = get_calendar_service()

        # Build start and end datetimes.
        start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        event = {
            "summary": title,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": "Africa/Cairo",
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Africa/Cairo",
            },
        }

        created = service.events().insert(
            calendarId="primary", body=event
        ).execute()

        return (
            f"Event '{title}' created for {date} at {start_time}. "
            f"Link: {created.get('htmlLink', 'n/a')}"
        )

    except ValueError:
        return ("ERROR: bad date/time format. "
                "Use date 'YYYY-MM-DD' and start_time 'HH:MM'.")
    except Exception as e:
        return f"ERROR creating event: {e}"