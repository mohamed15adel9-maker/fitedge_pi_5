"""
tools/wger.py

Reads strength-training data from wger (hosted at wger.de).

SETUP (one time):
  1. Free account at https://wger.de
  2. Log some workouts so there's data to read.
  3. Get your API token: wger.de > your account settings > API.
  4. Put it in auth/wger_secrets.json:
     {"token": "YOUR_API_TOKEN"}

Auth: a token in the Authorization header ("Token <token>").

Requires:
    pip install requests
"""

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


def _get_routine_id():
    """
    Find the user's routine ID.

    Preferred:
        Put {"routine_id": YOUR_ID, ...} in wger_secrets.json.

    Otherwise:
        Fetch the user's routines and use the first non-template
        routine returned by wger.
    """
    try:
        secrets = json.loads(
            SECRETS_FILE.read_text()
        )

        routine_id = secrets.get("routine_id")

        if routine_id:
            return routine_id

        resp = requests.get(
            f"{API_BASE}/routine/",
            headers=_headers(),
            params={"limit": 50},
            timeout=30,
        )
        resp.raise_for_status()

        routines = resp.json().get(
            "results",
            []
        )

        if not routines:
            return None

        # Prefer non-template routines.
        for routine in routines:
            if not (
                routine.get("template")
                or routine.get("is_template")
            ):
                if routine.get("id") is not None:
                    return routine["id"]

        # Fallback: first routine with an id.
        for routine in routines:
            if routine.get("id") is not None:
                return routine["id"]

        return None

    except Exception:
        return None


def _format_workout_log(log, exercise_cache):
    """
    Convert one wger workout log into a readable set description.
    Returns (exercise_id, exercise_name, set_text).
    """

    exercise = log.get("exercise")

    if isinstance(exercise, dict):
        exercise_id = exercise.get("id")
        exercise_name = (
            exercise.get("name")
            or exercise.get("name_en")
            or f"Exercise {exercise_id}"
        )
    else:
        exercise_id = exercise
        exercise_name = None

    # Resolve exercise name only when necessary.
    if (
        exercise_name is None
        and exercise_id is not None
    ):
        if exercise_id not in exercise_cache:
            exercise_resp = requests.get(
                f"{API_BASE}/exerciseinfo/{exercise_id}/",
                headers=_headers(),
                params={"format": "json"},
                timeout=30,
            )
            exercise_resp.raise_for_status()

            exercise_data = exercise_resp.json()

            # Prefer the English/localized human-readable name.
            exercise_name = None

            # Prefer an explicit English translation.
            translations = (
                exercise_data.get("translations")
                or []
            )

            for translation in translations:
                if not isinstance(
                    translation,
                    dict,
                ):
                    continue

                language_value = (
                    translation.get("language")
                    or translation.get("language_code")
                )

                # wger uses numeric language IDs in exerciseinfo.
                # Language ID 2 is English.
                language_text = str(
                    language_value or ""
                ).strip().lower()

                is_english = (
                    language_value == 2
                    or language_text in (
                        "2",
                        "en",
                        "eng",
                        "english",
                    )
                )

                if is_english:
                    candidate = translation.get("name")

                    if candidate:
                        exercise_name = candidate
                        break

            # Fallback to an explicitly English top-level field.
            if not exercise_name:
                exercise_name = exercise_data.get(
                    "name_en"
                )

            # If wger gives no English name, use the top-level name
            # only as a last resort.
            if not exercise_name:
                exercise_name = exercise_data.get(
                    "name"
                )

            exercise_cache[exercise_id] = (
                exercise_name
                or f"Exercise {exercise_id}"
            )

        exercise_name = exercise_cache[
            exercise_id
        ]

    if exercise_name is None:
        exercise_name = "Unknown exercise"

    repetitions = log.get("repetitions")
    weight = log.get("weight")
    rir = log.get("rir")

    if (
        repetitions is not None
        and weight is not None
    ):
        set_text = (
            f"{repetitions} x "
            f"{weight} kg"
        )
    elif repetitions is not None:
        set_text = f"{repetitions} reps"
    elif weight is not None:
        set_text = f"{weight} kg"
    else:
        set_text = "No reps/weight recorded"

    if rir is not None:
        set_text += f" (RiR {rir})"

    return (
        exercise_id,
        exercise_name,
        set_text,
    )


def _get_routine_logs(routine_id):
    """
    Fetch actual workout sessions/logs for one routine.

    Returns the API JSON or None when the routine-log endpoint
    is unavailable/empty.
    """
    resp = requests.get(
        f"{API_BASE}/routine/{routine_id}/logs/",
        headers=_headers(),
        timeout=30,
    )

    resp.raise_for_status()

    data = resp.json()

    if not data:
        return None

    return data


def get_recent_workouts(limit=5, return_structured=False):
    """
    Returns recent workout sessions including the actual
    exercises/sets logged for each session.

    First tries the routine logs endpoint.
    Falls back to the original workout-session/workout-log
    endpoints if needed.
    """

    try:
        # -------------------------------------------------
        # 1. Find the user's routine
        # -------------------------------------------------

        routine_id = _get_routine_id()

        # -------------------------------------------------
        # 2. Preferred: routine logs endpoint
        # -------------------------------------------------

        if routine_id is not None:
            try:
                routine_data = _get_routine_logs(
                    routine_id
                )

                if routine_data:
                    if isinstance(routine_data, dict):
                        sessions = routine_data.get(
                            "results",
                            routine_data.get(
                                "sessions",
                                [],
                            ),
                        )
                    elif isinstance(routine_data, list):
                        sessions = routine_data
                    else:
                        sessions = []

                    if sessions:
                        sessions = sorted(
                            sessions,
                            key=lambda s: (
                                s.get("date", "")
                                if isinstance(s, dict)
                                else ""
                            ),
                            reverse=True,
                        )[:limit]

                        lines = []
                        structured_sessions = []

                        for session in sessions:
                            if not isinstance(
                                session,
                                dict,
                            ):
                                continue

                            session_date = session.get(
                                "date",
                                "?",
                            )

                            notes = (
                                session.get(
                                    "notes",
                                    "",
                                )
                                or ""
                            )

                            impression = session.get(
                                "impression",
                                "",
                            )

                            impression_map = {
                                "1": "bad",
                                "2": "neutral",
                                "3": "good",
                            }

                            feel = impression_map.get(
                                str(impression),
                                "",
                            )

                            header = str(
                                session_date
                            )

                            if feel:
                                header += f" (felt {feel})"

                            if notes:
                                header += f": {notes}"

                            lines.append(header)

                            structured_session = {
                                "date": session_date,
                                "notes": notes,
                                "feel": feel,
                                "exercises": [],
                            }

                            logs = (
                                session.get("logs")
                                or session.get("workout_logs")
                                or session.get("results")
                                or []
                            )

                            if isinstance(logs, dict):
                                logs = logs.get(
                                    "results",
                                    [],
                                )

                            if not logs:
                                lines.append(
                                    "  No exercise logs recorded."
                                )
                                continue

                            exercise_cache = {}
                            exercise_groups = {}

                            for log in logs:
                                if not isinstance(
                                    log,
                                    dict,
                                ):
                                    continue

                                (
                                    exercise_id,
                                    exercise_name,
                                    set_text,
                                ) = _format_workout_log(
                                    log,
                                    exercise_cache,
                                )

                                key = (
                                    exercise_id,
                                    exercise_name,
                                )

                                exercise_groups.setdefault(
                                    key,
                                    [],
                                ).append(
                                    set_text
                                )

                            if not exercise_groups:
                                lines.append(
                                    "  No exercise logs recorded."
                                )
                                continue

                            for (
                                key,
                                set_texts,
                            ) in exercise_groups.items():

                                exercise_name = key[1]

                                lines.append(
                                    f"  {exercise_name}"
                                )

                                structured_session["exercises"].append({
                                    "id": key[0],
                                    "name": exercise_name,
                                    "sets": [
                                        {"description": set_text}
                                        for set_text in set_texts
                                    ],
                                })

                                for set_text in set_texts:
                                    lines.append(
                                        f"    {set_text}"
                                    )

                            structured_sessions.append(structured_session)

                        if lines:
                            result_text = "\n".join(lines)
                            if return_structured:
                                return result_text, structured_sessions
                            return result_text

            except Exception:
                # If the preferred routine endpoint fails,
                # continue to the original fallback method.
                pass

        # -------------------------------------------------
        # 3. Fallback: original session endpoint
        # -------------------------------------------------

        resp = requests.get(
            f"{API_BASE}/workoutsession/",
            headers=_headers(),
            params={
                "ordering": "-date",
                "limit": limit,
            },
            timeout=30,
        )

        resp.raise_for_status()

        sessions = resp.json().get(
            "results",
            [],
        )

        if not sessions:
            return (
                "No recent workout sessions "
                "found on wger."
            )

        lines = []
        structured_sessions = []

        for session in sessions:

            session_id = session.get("id")

            session_date = session.get(
                "date",
                "?",
            )

            notes = (
                session.get(
                    "notes",
                    "",
                )
                or ""
            )

            impression = session.get(
                "impression",
                "",
            )

            impression_map = {
                "1": "bad",
                "2": "neutral",
                "3": "good",
            }

            feel = impression_map.get(
                str(impression),
                "",
            )

            header = str(session_date)

            if feel:
                header += f" (felt {feel})"

            if notes:
                header += f": {notes}"

            lines.append(header)

            structured_session = {
                "date": session_date,
                "notes": notes,
                "feel": feel,
                "exercises": [],
            }

            try:
                log_resp = requests.get(
                    f"{API_BASE}/workoutlog/",
                    headers=_headers(),
                    params={
                        "session": session_id,
                        "limit": 500,
                    },
                    timeout=30,
                )

                log_resp.raise_for_status()

                logs = log_resp.json().get(
                    "results",
                    [],
                )

            except Exception:
                logs = []

            if not logs:
                lines.append(
                    "  No exercise logs recorded."
                )
                continue

            exercise_cache = {}
            exercise_groups = {}

            for log in logs:

                try:
                    (
                        exercise_id,
                        exercise_name,
                        set_text,
                    ) = _format_workout_log(
                        log,
                        exercise_cache,
                    )

                except Exception:
                    continue

                key = (
                    exercise_id,
                    exercise_name,
                )

                exercise_groups.setdefault(
                    key,
                    [],
                ).append(
                    set_text
                )

            if not exercise_groups:
                lines.append(
                    "  No exercise logs recorded."
                )
                continue

            for key, set_texts in (
                exercise_groups.items()
            ):

                exercise_name = key[1]

                lines.append(
                    f"  {exercise_name}"
                )

                structured_session["exercises"].append({
                    "id": key[0],
                    "name": exercise_name,
                    "sets": [
                        {"description": set_text}
                        for set_text in set_texts
                    ],
                })

                for set_text in set_texts:
                    lines.append(
                        f"    {set_text}"
                    )

            structured_sessions.append(structured_session)

        result_text = "\n".join(lines)
        if return_structured:
            return result_text, structured_sessions
        return result_text

    except Exception as e:
        return (
            f"ERROR reading wger workouts: {e}"
        )


def get_weight_log(limit=5, return_structured=False):
    """
    Returns recent bodyweight entries as readable text.
    """
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
        structured_entries = [
            {
                "date": e.get("date"),
                "weight": e.get("weight"),
            }
            for e in entries
        ]
        result_text = "\n".join(lines)
        if return_structured:
            return result_text, structured_entries
        return result_text

    except Exception as e:
        return f"ERROR reading wger weight log: {e}"


def add_weight_entry(weight, entry_date=None):
    """
    Adds a bodyweight entry. entry_date is 'YYYY-MM-DD' (defaults to today).
    """
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