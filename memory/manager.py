from memory.database import get_connection


# ==========================================================
# USERS
# ==========================================================

def create_user(name, age=None, sex=None, height=None):
    """Creates a new user and returns its id."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO users (name, age, sex, height)
        VALUES (?, ?, ?, ?)
        """,
        (name, age, sex, height),
    )
    connection.commit()
    user_id = cursor.lastrowid
    connection.close()
    return user_id


def get_user(user_id):
    """Returns a user by ID, or None."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    connection.close()
    return dict(user) if user else None


def get_all_users():
    """Returns every user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id")
    users = cursor.fetchall()
    connection.close()
    return [dict(user) for user in users]


def update_user(user_id, name=None, age=None, sex=None, height=None):
    """
    Updates an existing user. Only the fields you pass (non-None) are
    changed; anything left as None keeps its current value.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE users
        SET name   = COALESCE(?, name),
            age    = COALESCE(?, age),
            sex    = COALESCE(?, sex),
            height = COALESCE(?, height)
        WHERE id = ?
        """,
        (name, age, sex, height, user_id),
    )
    connection.commit()
    connection.close()


def delete_user(user_id):
    """Deletes a user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    connection.commit()
    connection.close()


# ==========================================================
# MEASUREMENTS
# ==========================================================

_MEASUREMENT_FIELDS = (
    "weight", "body_fat", "waist", "chest", "hips",
    "left_arm", "right_arm", "left_thigh", "right_thigh",
    "left_calf", "right_calf", "neck", "resting_heart_rate", "notes",
)


def create_measurement(
    user_id,
    weight=None, body_fat=None, waist=None, chest=None, hips=None,
    left_arm=None, right_arm=None, left_thigh=None, right_thigh=None,
    left_calf=None, right_calf=None, neck=None, resting_heart_rate=None,
    notes=None, date=None,
):
    """Saves a body measurement. Defaults the date to today if not given."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO measurements (
            user_id, date, weight, body_fat, waist, chest, hips,
            left_arm, right_arm, left_thigh, right_thigh,
            left_calf, right_calf, neck, resting_heart_rate, notes
        )
        VALUES (?, COALESCE(?, DATE('now')), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id, date, weight, body_fat, waist, chest, hips,
            left_arm, right_arm, left_thigh, right_thigh,
            left_calf, right_calf, neck, resting_heart_rate, notes,
        ),
    )
    connection.commit()
    measurement_id = cursor.lastrowid
    connection.close()
    return measurement_id


def get_measurement(measurement_id):
    """Returns a single measurement by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM measurements WHERE id = ?", (measurement_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_latest_measurement(user_id):
    """Returns the most recent body measurement for a user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM measurements
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_measurements(user_id, limit=None):
    """Returns a user's measurements, newest first. Optional limit."""
    connection = get_connection()
    cursor = connection.cursor()
    query = (
        "SELECT * FROM measurements WHERE user_id = ? "
        "ORDER BY date DESC, id DESC"
    )
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_measurement(measurement_id, **fields):
    """
    Updates any measurement columns passed as keyword arguments, e.g.
    update_measurement(3, weight=80.5, notes="post-cut").
    Unknown keys are ignored.
    """
    updates = {k: v for k, v in fields.items() if k in _MEASUREMENT_FIELDS}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [measurement_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"UPDATE measurements SET {set_clause} WHERE id = ?", params
    )
    connection.commit()
    connection.close()


def delete_measurement(measurement_id):
    """Deletes a measurement."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM measurements WHERE id = ?", (measurement_id,))
    connection.commit()
    connection.close()


# ==========================================================
# GOALS
# ==========================================================

_GOAL_FIELDS = (
    "title", "description", "priority", "status",
    "start_date", "target_date", "completed_date",
)


def create_goal(user_id, title, description=None, priority=None,
                status="active", start_date=None, target_date=None):
    """Creates a goal and returns its id. Defaults status to 'active'."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO goals
        (user_id, title, description, priority, status, start_date, target_date)
        VALUES (?, ?, ?, ?, ?, COALESCE(?, DATE('now')), ?)
        """,
        (user_id, title, description, priority, status, start_date, target_date),
    )
    connection.commit()
    goal_id = cursor.lastrowid
    connection.close()
    return goal_id


def get_goal(goal_id):
    """Returns a single goal by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_active_goals(user_id):
    """Returns a user's goals whose status is 'active', by priority."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM goals
        WHERE user_id = ? AND status = 'active'
        ORDER BY priority IS NULL, priority ASC, target_date ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_all_goals(user_id):
    """Returns all of a user's goals, newest first."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY id DESC", (user_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_goal(goal_id, **fields):
    """Updates any goal columns passed as keyword arguments."""
    updates = {k: v for k, v in fields.items() if k in _GOAL_FIELDS}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [goal_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE goals SET {set_clause} WHERE id = ?", params)
    connection.commit()
    connection.close()


def complete_goal(goal_id):
    """Marks a goal completed and stamps today's completion date."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE goals
        SET status = 'completed', completed_date = DATE('now')
        WHERE id = ?
        """,
        (goal_id,),
    )
    connection.commit()
    connection.close()


def delete_goal(goal_id):
    """Deletes a goal."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    connection.commit()
    connection.close()


# ==========================================================
# WORKOUTS
# ==========================================================

_WORKOUT_FIELDS = ("date", "workout_type", "duration", "calories", "notes")


def create_workout(user_id, workout_type=None, duration=None,
                   calories=None, notes=None, date=None):
    """Creates a workout and returns its id. Defaults date to today."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO workouts
        (user_id, date, workout_type, duration, calories, notes)
        VALUES (?, COALESCE(?, DATE('now')), ?, ?, ?, ?)
        """,
        (user_id, date, workout_type, duration, calories, notes),
    )
    connection.commit()
    workout_id = cursor.lastrowid
    connection.close()
    return workout_id


def get_workout(workout_id):
    """Returns a single workout by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_latest_workout(user_id):
    """Returns the user's most recent workout."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM workouts
        WHERE user_id = ?
        ORDER BY date DESC, id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_workouts(user_id, limit=None):
    """Returns a user's workouts, newest first. Optional limit."""
    connection = get_connection()
    cursor = connection.cursor()
    query = (
        "SELECT * FROM workouts WHERE user_id = ? "
        "ORDER BY date DESC, id DESC"
    )
    params = [user_id]
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_workout(workout_id, **fields):
    """Updates any workout columns passed as keyword arguments."""
    updates = {k: v for k, v in fields.items() if k in _WORKOUT_FIELDS}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [workout_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE workouts SET {set_clause} WHERE id = ?", params)
    connection.commit()
    connection.close()


def delete_workout(workout_id):
    """
    Deletes a workout and all of its exercises (since exercises belong
    to a workout).
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM exercises WHERE workout_id = ?", (workout_id,))
    cursor.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
    connection.commit()
    connection.close()


# ==========================================================
# EXERCISES
# ==========================================================

_EXERCISE_FIELDS = (
    "exercise_name", "sets", "reps", "weight", "rir", "rest_seconds",
)


def create_exercise(workout_id, exercise_name, sets=None, reps=None,
                    weight=None, rir=None, rest_seconds=None):
    """Adds an exercise to a workout and returns its id."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO exercises
        (workout_id, exercise_name, sets, reps, weight, rir, rest_seconds)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (workout_id, exercise_name, sets, reps, weight, rir, rest_seconds),
    )
    connection.commit()
    exercise_id = cursor.lastrowid
    connection.close()
    return exercise_id


def get_exercise(exercise_id):
    """Returns a single exercise by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM exercises WHERE id = ?", (exercise_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_exercises_for_workout(workout_id):
    """Returns all exercises belonging to a workout, in insertion order."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM exercises WHERE workout_id = ? ORDER BY id",
        (workout_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_exercise(exercise_id, **fields):
    """Updates any exercise columns passed as keyword arguments."""
    updates = {k: v for k, v in fields.items() if k in _EXERCISE_FIELDS}
    if not updates:
        return
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [exercise_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE exercises SET {set_clause} WHERE id = ?", params)
    connection.commit()
    connection.close()


def delete_exercise(exercise_id):
    """Deletes an exercise."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
    connection.commit()
    connection.close()


# ==========================================================
# INJURIES
# ==========================================================

_INJURY_FIELDS = ("body_part", "description", "severity", "date", "active")


def create_injury(user_id, body_part=None, description=None,
                  severity=None, date=None, active=True):
    """Records an injury and returns its id. Defaults date to today."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO injuries
        (user_id, body_part, description, severity, date, active)
        VALUES (?, ?, ?, ?, COALESCE(?, DATE('now')), ?)
        """,
        (user_id, body_part, description, severity, date, 1 if active else 0),
    )
    connection.commit()
    injury_id = cursor.lastrowid
    connection.close()
    return injury_id


def get_injury(injury_id):
    """Returns a single injury by ID."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM injuries WHERE id = ?", (injury_id,))
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_active_injuries(user_id):
    """Returns a user's currently active injuries."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM injuries
        WHERE user_id = ? AND active = 1
        ORDER BY date DESC, id DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_all_injuries(user_id):
    """Returns all of a user's injuries, newest first."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM injuries WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_injury(injury_id, **fields):
    """Updates any injury columns passed as keyword arguments."""
    updates = {k: v for k, v in fields.items() if k in _INJURY_FIELDS}
    if not updates:
        return
    # normalise the boolean if present
    if "active" in updates:
        updates["active"] = 1 if updates["active"] else 0
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [injury_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(f"UPDATE injuries SET {set_clause} WHERE id = ?", params)
    connection.commit()
    connection.close()


def resolve_injury(injury_id):
    """Marks an injury as no longer active (recovered)."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE injuries SET active = 0 WHERE id = ?", (injury_id,))
    connection.commit()
    connection.close()


def delete_injury(injury_id):
    """Deletes an injury."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM injuries WHERE id = ?", (injury_id,))
    connection.commit()
    connection.close()


# ==========================================================
# PREFERENCES
# ==========================================================

_PREFERENCE_FIELDS = ("language", "measurement_system", "tts_voice")


def create_preferences(user_id, language=None, measurement_system=None,
                       tts_voice=None):
    """
    Creates a preferences row for a user and returns its id.
    Typically there is one preferences row per user.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO preferences
        (user_id, language, measurement_system, tts_voice)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, language, measurement_system, tts_voice),
    )
    connection.commit()
    preferences_id = cursor.lastrowid
    connection.close()
    return preferences_id


def get_preferences(user_id):
    """Returns a user's preferences row, or None."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM preferences WHERE user_id = ? ORDER BY id LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def update_preferences(user_id, **fields):
    """
    Updates a user's preferences. Creates the row first if none exists,
    so callers don't have to check.
    """
    updates = {k: v for k, v in fields.items() if k in _PREFERENCE_FIELDS}
    if not updates:
        return
    if get_preferences(user_id) is None:
        create_preferences(user_id)
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    params = list(updates.values()) + [user_id]
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        f"UPDATE preferences SET {set_clause} WHERE user_id = ?", params
    )
    connection.commit()
    connection.close()


def delete_preferences(user_id):
    """Deletes a user's preferences."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
    connection.commit()
    connection.close()


# ==========================================================
# CONVERSATION MEMORY
# ==========================================================

def create_conversation(conversation_id, role, message,user_id):
    """
    Convenience alias for adding the first message of a conversation.
    Returns the new row id.
    """
    return add_message(conversation_id, role, message,user_id)


def add_message(conversation_id, role, message,user_id):
    """
    Appends a message to a conversation. `role` is typically 'user' or
    'assistant'. Returns the new row id.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO conversations (conversation_id, role, message,user_id)
        VALUES (?, ?, ?, ?)
        """,
        (conversation_id, role, message,user_id),
    )
    connection.commit()
    row_id = cursor.lastrowid
    connection.close()
    return row_id


def get_conversation(conversation_id):
    """Returns every message in a conversation, oldest first."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM conversations
        WHERE conversation_id = ?
        ORDER BY timestamp ASC, id ASC
        """,
        (conversation_id,),
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_recent_messages(conversation_id,user_id, limit=10):
    """
    Returns the most recent `limit` messages of a conversation, returned
    in chronological order (oldest of the recent batch first) so they can
    be fed straight into the model as context.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT * FROM conversations
        WHERE conversation_id = ?
        AND user_id = ? 
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        (conversation_id,user_id,limit),
    )
    rows = cursor.fetchall()
    connection.close()
    # reverse so the oldest of the recent batch comes first
    return [dict(row) for row in reversed(rows)]


def get_all_conversations(user_id):
    """Returns the distinct conversation ids with basic stats."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT conversation_id,
               COUNT(*)        AS message_count,
               MIN(timestamp)  AS started_at,
               MAX(timestamp)  AS last_at
        FROM conversations
        WHERE user_id = ?
        GROUP BY conversation_id
        ORDER BY last_at DESC
        """
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def clear_conversation(conversation_id):
    """
    Deletes all messages in a conversation (kept as a distinct name from
    delete_conversation for readability; both do the same thing).
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM conversations WHERE conversation_id = ?",
        (conversation_id,),
    )
    connection.commit()
    connection.close()


def delete_conversation(conversation_id):
    """Deletes an entire conversation."""
    clear_conversation(conversation_id)


# ==========================================================
# LONG TERM FACTS
# ==========================================================

def create_fact(user_id, key, value, confidence=1.0):
    """
    Stores a long-term fact about the user (e.g. key='hates',
    value='burpees'). If the same key already exists for the user it is
    updated instead of duplicated. Returns the fact id.
    """
    existing = get_fact(user_id, key)
    if existing is not None:
        update_fact(user_id, key, value, confidence)
        return existing["id"]

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO facts (user_id, key, value, confidence)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, key, value, confidence),
    )
    connection.commit()
    fact_id = cursor.lastrowid
    connection.close()
    return fact_id


def get_fact(user_id, key):
    """Returns a single fact for a user by key, or None."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM facts WHERE user_id = ? AND key = ? LIMIT 1",
        (user_id, key),
    )
    row = cursor.fetchone()
    connection.close()
    return dict(row) if row else None


def get_all_facts(user_id):
    """Returns all stored facts for a user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM facts WHERE user_id = ? ORDER BY key", (user_id,)
    )
    rows = cursor.fetchall()
    connection.close()
    return [dict(row) for row in rows]


def update_fact(user_id, key, value, confidence=None):
    """
    Updates the value (and optionally confidence) of an existing fact,
    stamping the update time.
    """
    connection = get_connection()
    cursor = connection.cursor()
    if confidence is None:
        cursor.execute(
            """
            UPDATE facts
            SET value = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND key = ?
            """,
            (value, user_id, key),
        )
    else:
        cursor.execute(
            """
            UPDATE facts
            SET value = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND key = ?
            """,
            (value, confidence, user_id, key),
        )
    connection.commit()
    connection.close()


def delete_fact(user_id, key):
    """Deletes a single fact by key."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "DELETE FROM facts WHERE user_id = ? AND key = ?", (user_id, key)
    )
    connection.commit()
    connection.close()


def delete_all_facts(user_id):
    """Deletes every fact for a user."""
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM facts WHERE user_id = ?", (user_id,))
    connection.commit()
    connection.close()