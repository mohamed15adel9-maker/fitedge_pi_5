
from memory.database import get_connection


USER_ID = 1


def get_active_goals():
    """Get the user's active fitness goals."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT title, target_date
            FROM goals
            WHERE user_id = ?
              AND status = 'active'
            ORDER BY target_date ASC
            LIMIT 10
            """,
            (USER_ID,),
        )

        rows = cursor.fetchall()

        if not rows:
            return "No active goals found."

        return "\n".join(
            f"Goal: {row['title']}, Target date: {row['target_date']}"
            for row in rows
        )

    finally:
        connection.close()


def get_latest_measurement():
    """Get the user's latest body measurement."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                date,
                weight,
                body_fat,
                waist,
                chest,
                hips,
                resting_heart_rate
            FROM measurements
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT 1
            """,
            (USER_ID,),
        )

        row = cursor.fetchone()

        if not row:
            return "No measurements found."

        return ", ".join(
            f"{key}: {row[key]}"
            for key in row.keys()
            if row[key] is not None
        )

    finally:
        connection.close()


def get_active_injuries():
    """Get the user's active injuries."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT body_part, description, severity, date
            FROM injuries
            WHERE user_id = ?
              AND active = 1
            ORDER BY date DESC
            LIMIT 10
            """,
            (USER_ID,),
        )

        rows = cursor.fetchall()

        if not rows:
            return "No active injuries found."

        return "\n".join(
            f"Body part: {row['body_part']}, "
            f"Description: {row['description']}, "
            f"Severity: {row['severity']}, "
            f"Date: {row['date']}"
            for row in rows
        )

    finally:
        connection.close()


def get_recent_workouts(limit=5):
    """Get the user's recent workouts."""

    limit = max(1, min(int(limit), 20))

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            f"""
            SELECT
                id,
                date,
                workout_type,
                duration,
                calories,
                notes
            FROM workouts
            WHERE user_id = ?
            ORDER BY date DESC
            LIMIT {limit}
            """,
            (USER_ID,),
        )

        rows = cursor.fetchall()

        if not rows:
            return "No workouts found."

        return "\n".join(
            f"Date: {row['date']}, "
            f"Type: {row['workout_type']}, "
            f"Duration: {row['duration']} minutes, "
            f"Calories: {row['calories']}"
            for row in rows
        )

    finally:
        connection.close()


def get_user_fact(key):
    """Get one stored fact about the user."""

    if not key:
        return "No fact key provided."

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT value
            FROM facts
            WHERE user_id = ?
              AND key = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (USER_ID, key),
        )

        row = cursor.fetchone()

        if not row:
            return f"No stored fact found for '{key}'."

        return str(row["value"])

    finally:
        connection.close()


def get_user_profile():
    """Get the user's basic profile."""

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT name, age, sex, height
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (USER_ID,),
        )

        row = cursor.fetchone()

        if not row:
            return "No user profile found."

        return ", ".join(
            f"{key}: {row[key]}"
            for key in row.keys()
            if row[key] is not None
        )

    finally:
        connection.close()

