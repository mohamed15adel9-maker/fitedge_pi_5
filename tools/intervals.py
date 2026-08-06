"""
tools/intervals.py

Reads training data from Intervals.icu (which your iPhone/Apple Health
data syncs into via the Intervals.icu Companion app).

SETUP (one time):
  1. Free account at https://intervals.icu
  2. Install the "Intervals.icu Companion" iPhone app, connect Apple Health
     so your workouts/wellness sync in.
  3. Get your API key: intervals.icu > Settings > Developer.
     Also note your athlete id (looks like "i12345", shown in settings/URL).
  4. Put them in auth/intervals_secrets.json:
     {"athlete_id": "i12345", "api_key": "YOUR_KEY"}

Auth is simple HTTP Basic: username "API_KEY", password = your key.

Requires:
    pip install requests
"""

import json
from pathlib import Path
from datetime import date, timedelta

import requests

AUTH_DIR = Path(__file__).resolve().parent.parent / "auth"
SECRETS_FILE = AUTH_DIR / "intervals_secrets.json"

API_BASE = "https://intervals.icu/api/v1"


def _load_secrets():
    if not SECRETS_FILE.exists():
        raise RuntimeError(
            "Missing auth/intervals_secrets.json with athlete_id and api_key."
        )
    data = json.loads(SECRETS_FILE.read_text())
    return data["athlete_id"], data["api_key"]


def get_recent_activities(days_back=14, limit=10):
    """
    Returns recent activities (runs, rides, workouts) as readable text.
    """
    try:
        athlete_id, api_key = _load_secrets()

        oldest = (date.today() - timedelta(days=days_back)).isoformat()
        newest = date.today().isoformat()

        resp = requests.get(
            f"{API_BASE}/athlete/{athlete_id}/activities",
            params={"oldest": oldest, "newest": newest},
            auth=("API_KEY", api_key),      # HTTP Basic auth
            timeout=30,
        )
        resp.raise_for_status()
        activities = resp.json()

        if not activities:
            return "No recent activities found on Intervals.icu."

        lines = []
        for a in activities[:limit]:
            name = a.get("name", "(untitled)")
            atype = a.get("type", "activity")
            dist_km = round((a.get("distance") or 0) / 1000, 2)
            minutes = round((a.get("moving_time") or 0) / 60)
            day = (a.get("start_date_local") or "")[:10]
            hr = a.get("average_heartrate")
            hr_str = f", avg HR {round(hr)}" if hr else ""
            lines.append(f"{day}: {name} ({atype}) - {dist_km} km, {minutes} min{hr_str}")

        return "\n".join(lines)

    except Exception as e:
        return f"ERROR reading Intervals.icu activities: {e}"


def get_wellness(days_back=7):
    """
    Returns recent wellness metrics (resting HR, HRV, sleep, etc.) as text.
    """
    try:
        athlete_id, api_key = _load_secrets()

        oldest = (date.today() - timedelta(days=days_back)).isoformat()
        newest = date.today().isoformat()

        resp = requests.get(
            f"{API_BASE}/athlete/{athlete_id}/wellness",
            params={"oldest": oldest, "newest": newest},
            auth=("API_KEY", api_key),
            timeout=30,
        )
        resp.raise_for_status()
        days = resp.json()

        if not days:
            return "No recent wellness data found."

        lines = []
        for d in days:
            day = d.get("id", "?")            # the date
            rhr = d.get("restingHR")
            hrv = d.get("hrv")
            sleep = d.get("sleepSecs")
            sleep_h = round(sleep / 3600, 1) if sleep else None
            parts = []
            if rhr:     parts.append(f"resting HR {rhr}")
            if hrv:     parts.append(f"HRV {hrv}")
            if sleep_h: parts.append(f"sleep {sleep_h}h")
            if parts:
                lines.append(f"{day}: " + ", ".join(parts))

        return "\n".join(lines) if lines else "No wellness values recorded."

    except Exception as e:
        return f"ERROR reading Intervals.icu wellness: {e}"
