

import json
from pathlib import Path

import requests

AUTH_DIR = Path(__file__).resolve().parent.parent / "auth"
SECRETS_FILE = AUTH_DIR / "wger_secrets.json"

API_BASE = "https://wger.de/api/v2"


def _headers():
    if not SECRETS_FILE.exists():
        raise RuntimeError("Missing auth/wger_secrets.json with your API token.")
    token = json.loads(SECRETS_FILE.read_text())["token"]
    return {"Authorization": f"Token {token}", "Accept": "application/json"}


def get_recent_workouts(limit=5):

    try:
        resp = requests.get(
            f"{API_BASE}/workoutsession/",
            headers=_headers(),
            params={"ordering": "-date", "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        sessions = resp.json().get("results", [])

        if not sessions:
            return "No recent workout sessions found on wger."

        lines = []
        for s in sessions:
            day = s.get("date", "?")
            notes = s.get("notes", "") or ""
            impression = s.get("impression", "")
            impression_map = {"1": "bad", "2": "neutral", "3": "good"}
            feel = impression_map.get(str(impression), "")
            line = f"{day}"
            if feel:
                line += f" (felt {feel})"
            if notes:
                line += f": {notes}"
            lines.append(line)

        return "\n".join(lines)

    except Exception as e:
        return f"ERROR reading wger workouts: {e}"


def get_weight_log(limit=5):
    
    try:
        resp = requests.get(
            f"{API_BASE}/weightentry/",
            headers=_headers(),
            params={"ordering": "-date", "limit": limit},
            timeout=30,
        )
        resp.raise_for_status()
        entries = resp.json().get("results", [])

        if not entries:
            return "No weight entries found on wger."

        lines = [f"{e.get('date','?')}: {e.get('weight','?')} kg" for e in entries]
        return "\n".join(lines)

    except Exception as e:
        return f"ERROR reading wger weight log: {e}"


def add_weight_entry(weight, entry_date=None):
    
    try:
        from datetime import date as _date
        payload = {
            "weight": weight,
            "date": entry_date or _date.today().isoformat(),
        }
        resp = requests.post(
            f"{API_BASE}/weightentry/",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return f"Weight entry added: {payload['weight']} kg on {payload['date']}."
    except Exception as e:
        return f"ERROR adding weight entry: {e}"