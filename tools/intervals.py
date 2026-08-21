"""
tools/intervals.py

Reads training data from Intervals.icu (your iPhone/Apple Health data syncs
in via the Intervals.icu Companion app).

Functions:
  - get_recent_activities(days_back, limit)  rich summary of recent activities
  - get_activity_details(activity_title, activity_date=None)  splits/intervals for one activity
  - get_wellness(days_back)                  full daily wellness + fitness stats

SETUP (one time):
  1. Free account at https://intervals.icu
  2. Companion iPhone app -> connect Apple Health so data syncs in.
  3. Settings > Developer Settings -> API key + athlete id ("i12345").
  4. auth/intervals_secrets.json:
     {"athlete_id": "i12345", "api_key": "YOUR_KEY"}

Auth: HTTP Basic, username "API_KEY", password = your key.
"""

import json
from pathlib import Path
from datetime import date, timedelta

import requests

AUTH_DIR = Path(__file__).resolve().parent.parent / "auth"
SECRETS_FILE = AUTH_DIR / "intervals_secrets.json"
API_BASE = "https://intervals.icu/api/v1"

# Rich set of summary fields to request per activity. Only those that exist
# on a given activity come back; the rest are simply absent.
ACTIVITY_FIELDS = ",".join([
    "id", "name", "type", "start_date_local",
    "distance", "moving_time", "elapsed_time",
    "total_elevation_gain",
    "average_speed", "max_speed",
    "average_heartrate", "max_heartrate",
    "average_cadence",
    "average_watts", "max_watts", "icu_weighted_avg_watts",
    "calories",
    "icu_training_load", "icu_intensity",
    "icu_zone_times",
    "pace", "gap",  # grade-adjusted pace
    "feel", "icu_rpe",
])


def _load_secrets():
    if not SECRETS_FILE.exists():
        raise RuntimeError(
            "Missing auth/intervals_secrets.json with athlete_id and api_key."
        )
    data = json.loads(SECRETS_FILE.read_text())
    return data["athlete_id"], data["api_key"]


def _auth():
    _, api_key = _load_secrets()
    return ("API_KEY", api_key)


def _fmt_duration(seconds):
    """Seconds -> 'Hh Mm' or 'Mm', guarding against absurd values."""
    if not seconds or seconds <= 0:
        return "?"
    minutes = int(seconds // 60)
    # guard obvious bad data (e.g. a stuck timer showing thousands of minutes)
    if minutes > 24 * 60:
        return f"{minutes} min (check data)"
    if minutes >= 60:
        return f"{minutes // 60}h {minutes % 60}m"
    return f"{minutes} min"


def _fmt_pace(speed_mps):
    """Metres/second -> running pace 'M:SS /km'."""
    if not speed_mps or speed_mps <= 0:
        return None
    sec_per_km = 1000.0 / speed_mps
    m = int(sec_per_km // 60)
    s = int(round(sec_per_km % 60))
    if s == 60:
        m, s = m + 1, 0
    return f"{m}:{s:02d} /km"


def get_recent_activities(days_back=14, limit=10, return_structured=False):
    """Rich summary of recent activities."""
    try:
        athlete_id, _ = _load_secrets()
        oldest = (date.today() - timedelta(days=days_back)).isoformat()
        newest = date.today().isoformat()

        resp = requests.get(
            f"{API_BASE}/athlete/{athlete_id}/activities",
            params={"oldest": oldest, "newest": newest, "fields": ACTIVITY_FIELDS},
            auth=_auth(),
            timeout=30,
        )
        resp.raise_for_status()
        activities = resp.json()
        if not activities:
            return "No recent activities found on Intervals.icu."

        lines = []
        structured_activities = []
        for a in activities[:limit]:
            day = (a.get("start_date_local") or "")[:10]
            name = a.get("name", "(untitled)")
            atype = a.get("type", "activity")
            aid = a.get("id", "")

            parts = [f"{day}: {name} ({atype}) [id {aid}]"]

            dist = a.get("distance")
            if dist:
                parts.append(f"{round(dist/1000, 2)} km")

            parts.append(_fmt_duration(a.get("moving_time")))

            pace = _fmt_pace(a.get("average_speed"))
            if pace and atype.lower() in ("run", "virtualrun", "walk", "hike"):
                parts.append(pace)

            elev = a.get("total_elevation_gain")
            if elev:
                parts.append(f"↑{round(elev)} m")

            hr = a.get("average_heartrate")
            if hr:
                mhr = a.get("max_heartrate")
                parts.append(f"HR {round(hr)}" + (f"/{round(mhr)}" if mhr else ""))

            watts = a.get("average_watts")
            if watts:
                parts.append(f"{round(watts)} W")

            cad = a.get("average_cadence")
            if cad:
                parts.append(f"cad {round(cad)}")

            load = a.get("icu_training_load")
            if load:
                parts.append(f"load {round(load)}")

            cal = a.get("calories")
            if cal:
                parts.append(f"{round(cal)} kcal")

            feel = a.get("feel")
            if feel:
                parts.append(f"feel {feel}/5")

            lines.append(" - ".join(parts))
            structured_activities.append(dict(a))

        result_text = "\n".join(lines)
        if return_structured:
            return result_text, structured_activities
        return result_text

    except Exception as e:
        return f"ERROR reading Intervals.icu activities: {e}"


def get_activity_details(
    activity_title=None,
    activity_date=None,
    return_structured=False,
):
    """
    Detailed breakdown of ONE activity, including its intervals/splits.

    Identify the activity by:
      - activity_title
      - activity_date
      - or both

    If both are provided, both are used to find the activity.

    If only a date is provided:
      - one activity on that date -> use it
      - multiple activities -> return the available activities
        and ask for the activity title
    """
    try:
        # -------------------------------------------------
        # 1. Validate input
        # -------------------------------------------------
        if not activity_title and not activity_date:
            return (
                "ERROR: Provide an activity title, "
                "an activity date, or both."
            )

        athlete_id, _ = _load_secrets()

        # If a date is provided, only request that date.
        # Otherwise search the last 90 days by title.
        oldest = (
            activity_date
            or (date.today() - timedelta(days=90)).isoformat()
        )
        newest = activity_date or date.today().isoformat()

        resp = requests.get(
            f"{API_BASE}/athlete/{athlete_id}/activities",
            params={
                "oldest": oldest,
                "newest": newest,
                "fields": ACTIVITY_FIELDS,
            },
            auth=_auth(),
            timeout=30,
        )
        resp.raise_for_status()
        activities = resp.json()

        matches = []

        wanted_title = (
            activity_title.strip().casefold()
            if activity_title
            else None
        )

        for activity in activities:
            name = (
                activity.get("name")
                or ""
            ).strip()

            day = (
                activity.get("start_date_local")
                or ""
            )[:10]

            # Date filter
            if activity_date and day != activity_date:
                continue

            # Title filter, only when a title was provided.
            if (
                wanted_title is not None
                and name.casefold() != wanted_title
            ):
                continue

            if activity.get("id") is not None:
                matches.append(
                    {
                        "id": activity["id"],
                        "date": day,
                        "name": name,
                        "type": activity.get(
                            "type",
                            "activity",
                        ),
                    }
                )

        # -------------------------------------------------
        # 2. No matches
        # -------------------------------------------------
        if not matches:
            if activity_title and activity_date:
                return (
                    f"No activity titled "
                    f"'{activity_title}' found on "
                    f"{activity_date}."
                )

            if activity_date:
                return (
                    f"No activities found on "
                    f"{activity_date}."
                )

            return (
                f"No activity titled "
                f"'{activity_title}' found in "
                "the last 90 days."
            )

        # -------------------------------------------------
        # 3. Multiple matches
        # -------------------------------------------------
        if len(matches) > 1:
            lines = []

            if activity_date and not activity_title:
                lines.append(
                    f"Multiple activities were found on "
                    f"{activity_date}:"
                )
            else:
                lines.append(
                    f"Multiple activities titled "
                    f"'{activity_title}' were found:"
                )

            for match in matches[:10]:
                label = match["name"] or "(untitled)"
                lines.append(
                    f"- {match['date']}: "
                    f"{label} ({match['type']})"
                )

            if activity_date and not activity_title:
                lines.append(
                    "Please provide the activity title."
                )
            else:
                lines.append(
                    "Please provide the activity date."
                )

            return "\n".join(lines)

        # -------------------------------------------------
        # 4. Exactly one match -> get full details
        # -------------------------------------------------
        activity_id = matches[0]["id"]

        resp = requests.get(
            f"{API_BASE}/activity/{activity_id}",
            params={"intervals": "true"},
            auth=_auth(),
            timeout=30,
        )
        resp.raise_for_status()
        a = resp.json()

        day = (
            a.get("start_date_local")
            or ""
        )[:10]

        name = (
            a.get("name")
            or "(untitled)"
        )

        atype = a.get(
            "type",
            "activity",
        )

        out = [
            f"{name} ({atype}) on {day}"
        ]

        if a.get("distance"):
            out.append(
                f"Distance: "
                f"{round(a['distance'] / 1000, 2)} km"
            )

        out.append(
            f"Moving time: "
            f"{_fmt_duration(a.get('moving_time'))}"
        )

        if a.get("elapsed_time"):
            out.append(
                f"Elapsed time: "
                f"{_fmt_duration(a.get('elapsed_time'))}"
            )

        if a.get("total_elevation_gain"):
            out.append(
                f"Elevation gain: "
                f"{round(a['total_elevation_gain'])} m"
            )

        if a.get("average_heartrate"):
            out.append(
                f"Avg/Max HR: "
                f"{round(a['average_heartrate'])}"
                f"/{round(a.get('max_heartrate') or 0)}"
            )

        if a.get("average_speed"):
            pace = _fmt_pace(
                a["average_speed"]
            )

            if pace:
                out.append(
                    f"Average pace: {pace}"
                )

        if a.get("average_watts"):
            out.append(
                f"Average power: "
                f"{round(a['average_watts'])} W"
            )

        if a.get("max_watts"):
            out.append(
                f"Max power: "
                f"{round(a['max_watts'])} W"
            )

        if a.get("icu_weighted_avg_watts"):
            out.append(
                f"Weighted average power: "
                f"{round(a['icu_weighted_avg_watts'])} W"
            )

        if a.get("average_cadence"):
            out.append(
                f"Average cadence: "
                f"{round(a['average_cadence'])}"
            )

        if a.get("calories"):
            out.append(
                f"Calories: "
                f"{round(a['calories'])} kcal"
            )

        if a.get("icu_training_load"):
            out.append(
                f"Training load: "
                f"{round(a['icu_training_load'])}"
            )

        if a.get("icu_intensity"):
            out.append(
                f"Intensity: "
                f"{a['icu_intensity']}"
            )

        if a.get("feel"):
            out.append(
                f"Feel: "
                f"{a['feel']}/5"
            )

        if a.get("icu_rpe"):
            out.append(
                f"RPE: "
                f"{a['icu_rpe']}"
            )

        # -------------------------------------------------
        # intervals / laps
        # -------------------------------------------------
        intervals = (
            a.get("icu_intervals")
            or a.get("intervals")
            or []
        )

        if intervals:
            out.append(
                "\nSplits / intervals:"
            )

            for i, iv in enumerate(
                intervals,
                1,
            ):
                label = (
                    iv.get("label")
                    or iv.get("type")
                    or f"Interval {i}"
                )

                seg = []

                if iv.get("distance"):
                    seg.append(
                        f"{round(iv['distance'] / 1000, 2)} km"
                    )

                if iv.get("moving_time"):
                    seg.append(
                        _fmt_duration(
                            iv["moving_time"]
                        )
                    )

                sp = _fmt_pace(
                    iv.get("average_speed")
                )

                if sp:
                    seg.append(sp)

                if iv.get("average_heartrate"):
                    seg.append(
                        f"HR {round(iv['average_heartrate'])}"
                    )

                if iv.get("average_watts"):
                    seg.append(
                        f"{round(iv['average_watts'])} W"
                    )

                out.append(
                    f"  {label}: "
                    + (
                        ", ".join(seg)
                        if seg
                        else "no metrics"
                    )
                )

        result_text = "\n".join(out)
        if return_structured:
            return result_text, a
        return result_text

    except Exception as e:
        return (
            f"ERROR reading activity details: {e}"
        )

def get_wellness(days_back=7, return_structured=False):
    """Full daily wellness + computed fitness (CTL/ATL/form)."""
    try:
        athlete_id, _ = _load_secrets()
        oldest = (date.today() - timedelta(days=days_back)).isoformat()
        newest = date.today().isoformat()

        resp = requests.get(
            f"{API_BASE}/athlete/{athlete_id}/wellness",
            params={"oldest": oldest, "newest": newest},
            auth=_auth(),
            timeout=30,
        )
        resp.raise_for_status()
        days = resp.json()
        if not days:
            return "No recent wellness data found."

        lines = []
        structured_days = []
        for d in days:
            day = d.get("id", "?")
            parts = []

            if d.get("weight"):        parts.append(f"weight {d['weight']} kg")
            if d.get("restingHR"):     parts.append(f"resting HR {d['restingHR']}")
            if d.get("hrv"):           parts.append(f"HRV {d['hrv']}")
            sleep = d.get("sleepSecs")
            if sleep:                  parts.append(f"sleep {round(sleep/3600, 1)}h")
            if d.get("sleepScore"):    parts.append(f"sleep score {d['sleepScore']}")
            if d.get("soreness"):      parts.append(f"soreness {d['soreness']}")
            if d.get("fatigue"):       parts.append(f"fatigue {d['fatigue']}")
            if d.get("stress"):        parts.append(f"stress {d['stress']}")
            if d.get("mood"):          parts.append(f"mood {d['mood']}")
            if d.get("steps"):         parts.append(f"{d['steps']} steps")
            # computed fitness metrics
            if d.get("ctl") is not None: parts.append(f"fitness/CTL {round(d['ctl'])}")
            if d.get("atl") is not None: parts.append(f"fatigue/ATL {round(d['atl'])}")
            if d.get("ctl") is not None and d.get("atl") is not None:
                parts.append(f"form/TSB {round(d['ctl'] - d['atl'])}")

            if parts:
                lines.append(f"{day}: " + ", ".join(parts))
                structured = dict(d)
                structured["date"] = day
                if structured.get("ctl") is not None and structured.get("atl") is not None:
                    structured["tsb"] = structured["ctl"] - structured["atl"]
                structured_days.append(structured)

        if not lines:
            return "No wellness values recorded."

        result_text = "\n".join(lines)
        if return_structured:
            return result_text, structured_days
        return result_text

    except Exception as e:
        return f"ERROR reading Intervals.icu wellness: {e}"