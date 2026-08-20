"""
display/data.py

Formats fetched/personal data for the 128x64 OLED.

The display is intentionally highly summarized.
The OLED is not intended to reproduce the complete API response.
"""

import ast

from PIL import Image, ImageDraw, ImageFont

from display.oled_faces import oled, WIDTH, HEIGHT


# =========================================================
# DISPLAY LIMITS
# =========================================================

FONT = ImageFont.load_default()

MAX_LINES = 5
LINE_HEIGHT = 11
MAX_CHARS = 21


# =========================================================
# BASIC HELPERS
# =========================================================

def _clean(value):
    if value is None:
        return ""

    return str(value).strip()


def _shorten(value, max_length=MAX_CHARS):
    value = _clean(value)

    if len(value) <= max_length:
        return value

    return value[:max_length - 3] + "..."


def _number(value):
    try:
        number = float(value)

        if number.is_integer():
            return str(int(number))

        return f"{number:.1f}"

    except (TypeError, ValueError):
        return _clean(value)


def _get(data, *keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data and data[key] is not None:
            return data[key]

    return default


def _unwrap(data, *keys):
    if not isinstance(data, dict):
        return data

    for key in keys:
        if key in data:
            return data[key]

    return data


# =========================================================
# GOALS
# =========================================================

def format_goals(data):

    goals = _unwrap(
        data,
        "goals",
        "results",
        "items",
    )

    if isinstance(goals, dict):
        goals = [goals]

    if not isinstance(goals, list):
        return [
            "GOALS",
            _shorten(goals),
        ]

    lines = ["GOALS"]

    for goal in goals[:4]:

        if isinstance(goal, dict):

            title = _get(
                goal,
                "title",
                "name",
                "goal",
                default="Goal",
            )

            status = _get(
                goal,
                "status",
                default="",
            )

            title = _shorten(title, 18)

            if status and str(status).lower() != "active":
                lines.append(
                    f"{title} {_shorten(status, 7)}"
                )
            else:
                lines.append(title)

        else:
            lines.append(
                _shorten(goal)
            )

    return lines


# =========================================================
# MEASUREMENTS
# =========================================================

def format_measurement(data):

    data = _unwrap(
        data,
        "measurement",
        "measurements",
        "result",
    )

    if isinstance(data, list):
        data = data[0] if data else {}

    if not isinstance(data, dict):
        return [
            "MEASURE",
            _shorten(data),
        ]

    lines = ["MEASURE"]

    weight = _get(
        data,
        "weight",
        "body_weight",
    )

    body_fat = _get(
        data,
        "body_fat",
        "bodyfat",
    )

    resting_hr = _get(
        data,
        "resting_heart_rate",
        "resting_hr",
        "heart_rate",
    )

    if weight is not None:
        lines.append(
            f"{_number(weight)}kg"
        )

    if body_fat is not None:
        lines.append(
            f"BF {_number(body_fat)}%"
        )

    if resting_hr is not None:
        lines.append(
            f"RHR {_number(resting_hr)}"
        )

    return lines


# =========================================================
# INJURIES
# =========================================================

def format_injuries(data):

    injuries = _unwrap(
        data,
        "injuries",
        "results",
        "items",
    )

    if isinstance(injuries, dict):
        injuries = [injuries]

    if not isinstance(injuries, list):
        return [
            "INJURY",
            _shorten(injuries),
        ]

    lines = ["INJURIES"]

    for injury in injuries[:4]:

        if isinstance(injury, dict):

            body_part = _get(
                injury,
                "body_part",
                "bodypart",
                "area",
                default="Unknown",
            )

            severity = _get(
                injury,
                "severity",
                default="",
            )

            text = _shorten(
                body_part,
                14,
            )

            if severity:
                text += " " + _shorten(
                    severity,
                    6,
                )

            lines.append(text)

        else:
            lines.append(
                _shorten(injury)
            )

    return lines


# =========================================================
# PROFILE
# =========================================================

def format_profile(data):

    data = _unwrap(
        data,
        "user",
        "profile",
    )

    if not isinstance(data, dict):
        return [
            "PROFILE",
            _shorten(data),
        ]

    lines = ["PROFILE"]

    name = _get(data, "name")
    age = _get(data, "age")
    height = _get(data, "height")

    if name:
        lines.append(
            _shorten(name)
        )

    if age is not None:
        lines.append(
            f"AGE {_number(age)}"
        )

    if height is not None:
        lines.append(
            f"HT {_number(height)}cm"
        )

    return lines


# =========================================================
# FACT
# =========================================================

def format_fact(data):

    if not isinstance(data, dict):
        return [
            "FACT",
            _shorten(data),
        ]

    key = _get(
        data,
        "key",
        default="FACT",
    )

    value = _get(
        data,
        "value",
        default="",
    )

    return [
        _shorten(
            str(key).upper(),
            21,
        ),
        _shorten(value, 21),
    ]


# =========================================================
# CALENDAR
# =========================================================

def format_calendar(data):

    events = _unwrap(
        data,
        "events",
        "items",
        "calendar",
    )

    if isinstance(events, dict):
        events = [events]

    if not isinstance(events, list):
        return [
            "CALENDAR",
            _shorten(events),
        ]

    lines = ["TODAY"]

    for event in events[:4]:

        if not isinstance(event, dict):
            lines.append(
                _shorten(event)
            )
            continue

        title = _get(
            event,
            "title",
            "summary",
            "name",
            default="Event",
        )

        start = _get(
            event,
            "start_time",
            "start",
            "time",
            default="",
        )

        title = _shorten(
            title,
            14,
        )

        start = _clean(start)

        if "T" in start:
            start = start.split("T")[-1]

        start = start[:5]

        if start:
            lines.append(
                f"{start} {title}"
            )
        else:
            lines.append(title)

    return lines


# =========================================================
# WORKOUTS
# =========================================================

def format_workouts(data):

    workouts = _unwrap(
        data,
        "workouts",
        "results",
        "items",
    )

    if isinstance(workouts, dict):
        workouts = [workouts]

    if not isinstance(workouts, list):
        return [
            "WORKOUTS",
            _shorten(workouts),
        ]

    lines = ["WORKOUTS"]

    for workout in workouts[:4]:

        if isinstance(workout, dict):

            name = _get(
                workout,
                "name",
                "title",
                "description",
                "workout_name",
                default="Workout",
            )

            lines.append(
                _shorten(name)
            )

        else:
            lines.append(
                _shorten(workout)
            )

    return lines


# =========================================================
# WEIGHT LOG
# =========================================================

def format_weight_log(data):

    entries = _unwrap(
        data,
        "weight_log",
        "weights",
        "entries",
        "results",
    )

    if isinstance(entries, dict):
        entries = [entries]

    if not isinstance(entries, list):
        return [
            "WEIGHT",
            _shorten(entries),
        ]

    lines = ["WEIGHT"]

    for entry in entries[:4]:

        if isinstance(entry, dict):

            weight = _get(
                entry,
                "weight",
                "body_weight",
            )

            date = _get(
                entry,
                "entry_date",
                "date",
            )

            if weight is None:
                continue

            if date:
                date = _clean(date)

                if "T" in date:
                    date = date.split("T")[0]

                if "-" in date:
                    parts = date.split("-")

                    if len(parts) >= 3:
                        date = (
                            f"{parts[-2]}/{parts[-1]}"
                        )

                lines.append(
                    f"{date} {_number(weight)}kg"
                )

            else:
                lines.append(
                    f"{_number(weight)}kg"
                )

        else:
            lines.append(
                _shorten(entry)
            )

    return lines


# =========================================================
# ACTIVITIES
# =========================================================

def format_activities(data):

    activities = _unwrap(
        data,
        "activities",
        "activity",
        "results",
        "items",
    )

    if isinstance(activities, dict):
        activities = [activities]

    if not isinstance(activities, list):
        return [
            "ACTIVITY",
            _shorten(activities),
        ]

    lines = ["ACTIVITY"]

    for activity in activities[:4]:

        if not isinstance(activity, dict):
            lines.append(
                _shorten(activity)
            )
            continue

        name = _get(
            activity,
            "name",
            "type",
            "sport",
            "activity_type",
            default="Activity",
        )

        distance = _get(
            activity,
            "distance",
            "distance_km",
        )

        duration = _get(
            activity,
            "duration",
            "moving_time",
        )

        name = _shorten(
            name,
            10,
        )

        if distance is not None:
            line = (
                f"{name} "
                f"{_number(distance)}km"
            )
        else:
            line = name

        if duration is not None:
            line += " " + _shorten(
                duration,
                7,
            )

        lines.append(
            _shorten(line)
        )

    return lines


# =========================================================
# WELLNESS
# =========================================================

def format_wellness(data):

    wellness = _unwrap(
        data,
        "wellness",
        "results",
        "data",
    )

    if isinstance(wellness, list):
        wellness = (
            wellness[0]
            if wellness
            else {}
        )

    if not isinstance(wellness, dict):
        return [
            "WELLNESS",
            _shorten(wellness),
        ]

    lines = ["WELLNESS"]

    sleep = _get(
        wellness,
        "sleep",
        "sleep_hours",
    )

    readiness = _get(
        wellness,
        "readiness",
        "recovery",
    )

    resting_hr = _get(
        wellness,
        "resting_heart_rate",
        "resting_hr",
    )

    if sleep is not None:
        lines.append(
            f"SLEEP {_number(sleep)}h"
        )

    if readiness is not None:
        lines.append(
            f"READY {_number(readiness)}"
        )

    if resting_hr is not None:
        lines.append(
            f"RHR {_number(resting_hr)}"
        )

    return lines


# =========================================================
# WEATHER
# =========================================================

def format_weather(data):

    if isinstance(data, dict):

        temperature = _get(
            data,
            "temperature_2m",
            "temperature",
            "temp",
        )

        apparent = _get(
            data,
            "apparent_temperature",
            "apparent_temperature_2m",
        )

        humidity = _get(
            data,
            "relative_humidity_2m",
            "humidity",
        )

        wind = _get(
            data,
            "wind_speed_10m",
            "wind_speed",
            "windspeed",
        )

        weather_code = _get(
            data,
            "weather_code",
            "weathercode",
        )

        lines = ["WEATHER"]

        if temperature is not None:

            line = (
                f"{_number(temperature)}C"
            )

            if apparent is not None:
                line += (
                    f" FEEL "
                    f"{_number(apparent)}C"
                )

            lines.append(
                _shorten(line)
            )

        if wind is not None:
            lines.append(
                f"WIND {_number(wind)}"
            )

        elif humidity is not None:
            lines.append(
                f"HUM {_number(humidity)}%"
            )

        if weather_code is not None:
            lines.append(
                f"CODE {weather_code}"
            )

        return lines

    return [
        "WEATHER",
        _shorten(data),
    ]


# =========================================================
# GENERIC FALLBACK
# =========================================================

def format_generic(data):

    if isinstance(data, dict):

        lines = ["DATA"]

        for key, value in data.items():

            if value is None:
                continue

            if isinstance(
                value,
                (dict, list, tuple),
            ):
                continue

            key = (
                str(key)
                .replace("_", " ")
                .upper()
            )

            key = _shorten(
                key,
                9,
            )

            value = _shorten(
                value,
                11,
            )

            lines.append(
                f"{key}:{value}"
            )

            if len(lines) >= MAX_LINES:
                break

        return lines

    if isinstance(data, list):

        return (
            ["DATA"]
            + [
                _shorten(item)
                for item in data[:MAX_LINES - 1]
            ]
        )

    return [
        "DATA",
        _shorten(data),
    ]


# =========================================================
# FORMATTER MAP
# =========================================================

FORMATTERS = {
    "goals": format_goals,
    "measurement": format_measurement,
    "injuries": format_injuries,
    "profile": format_profile,
    "fact": format_fact,
    "calendar": format_calendar,
    "workouts": format_workouts,
    "weight_log": format_weight_log,
    "activities": format_activities,
    "wellness": format_wellness,
    "weather": format_weather,
}


# =========================================================
# MAIN DISPLAY FUNCTION
# =========================================================

def show_data(data, display_type=None):
    """
    Format and display tool data on the 128x64 OLED.

    display_type is supplied by executor.py so we do not
    have to guess what kind of data we received.
    """

    if data is None:
        return

    # -----------------------------------------------------
    # Recover structured data if it arrived as a string.
    # -----------------------------------------------------

    if isinstance(data, str):

        text = data.strip()

        if not text:
            return

        try:
            parsed = ast.literal_eval(text)

            if isinstance(
                parsed,
                (dict, list),
            ):
                data = parsed

        except (
            ValueError,
            SyntaxError,
        ):
            data = text

    # -----------------------------------------------------
    # Select formatter
    # -----------------------------------------------------

    formatter = FORMATTERS.get(
        display_type,
        format_generic,
    )

    try:
        lines = formatter(data)

    except Exception as e:

        print(
            f"Display formatting error: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        lines = [
            "DATA",
            "DISPLAY ERROR",
        ]

    # -----------------------------------------------------
    # Final safety limits
    # -----------------------------------------------------

    clean_lines = []

    for line in lines:

        line = _clean(line)

        if not line:
            continue

        clean_lines.append(
            _shorten(
                line,
                MAX_CHARS,
            )
        )

    clean_lines = clean_lines[:MAX_LINES]

    if not clean_lines:
        clean_lines = ["DATA"]

    # -----------------------------------------------------
    # Create OLED image
    # -----------------------------------------------------

    image = Image.new(
        "1",
        (WIDTH, HEIGHT),
        0,
    )

    draw = ImageDraw.Draw(image)

    # -----------------------------------------------------
    # Draw
    # -----------------------------------------------------

    for index, line in enumerate(clean_lines):

        y = index * LINE_HEIGHT

        draw.text(
            (2, y),
            line,
            font=FONT,
            fill=1,
        )

    oled.display(image)

    print(
        "Display:",
        " | ".join(clean_lines),
        flush=True,
    )
