SCHEMA = """

-- ==========================================================
-- USERS
-- ==========================================================

CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    age INTEGER,

    sex TEXT,

    height REAL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);

-- ==========================================================
-- MEASUREMENTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS measurements (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    date DATE NOT NULL,

    weight REAL,

    body_fat REAL,

    waist REAL,

    chest REAL,

    hips REAL,

    left_arm REAL,

    right_arm REAL,

    left_thigh REAL,

    right_thigh REAL,

    left_calf REAL,

    right_calf REAL,

    neck REAL,

    resting_heart_rate INTEGER,

    notes TEXT,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- GOALS
-- ==========================================================

CREATE TABLE IF NOT EXISTS goals (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    title TEXT NOT NULL,

    description TEXT,

    priority INTEGER,

    status TEXT,

    start_date DATE,

    target_date DATE,

    completed_date DATE,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- WORKOUTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS workouts (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    date DATE NOT NULL,

    workout_type TEXT,

    duration INTEGER,

    calories INTEGER,

    notes TEXT,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- EXERCISES
-- ==========================================================

CREATE TABLE IF NOT EXISTS exercises (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    workout_id INTEGER NOT NULL,

    exercise_name TEXT NOT NULL,

    sets INTEGER,

    reps INTEGER,

    weight REAL,

    rir REAL,

    rest_seconds INTEGER,

    FOREIGN KEY(workout_id) REFERENCES workouts(id)

);

-- ==========================================================
-- INJURIES
-- ==========================================================

CREATE TABLE IF NOT EXISTS injuries (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    body_part TEXT,

    description TEXT,

    severity TEXT,

    date DATE,

    active BOOLEAN,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- PREFERENCES
-- ==========================================================

CREATE TABLE IF NOT EXISTS preferences (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    language TEXT,

    measurement_system TEXT,

    tts_voice TEXT,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- CONVERSATION MEMORY
-- ==========================================================

CREATE TABLE IF NOT EXISTS conversations (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    conversation_id TEXT NOT NULL,

    user_id INTEGER,

    role TEXT NOT NULL,

    message TEXT NOT NULL,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

-- ==========================================================
-- LONG TERM FACTS
-- ==========================================================

CREATE TABLE IF NOT EXISTS facts (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,

    key TEXT NOT NULL,

    value TEXT NOT NULL,

    confidence REAL DEFAULT 1.0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(user_id) REFERENCES users(id)

);

"""