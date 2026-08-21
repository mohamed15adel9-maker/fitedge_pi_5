"""
brain/llm.py

Hybrid FitEdge brain with MULTI-DOMAIN routing:
  - route_request(): classify into ONE OR MORE domains (returns a list)
  - tool groups: the model sees the tools of all relevant domains
  - native Ollama tool calling (no JSON round-trip)
  - the bounded multi-tool loop lives in agent.py and calls chat_with_tools()
  - build_context()/RAG/facts/history only at the final-answer stage

think=False everywhere (qwen is a thinking model; we want direct output).
"""

import json
import ollama

MODEL = "qwen3.5:2b"   # <-- must match `ollama list` exactly

# =========================================================
# NATIVE TOOL DEFINITIONS
# =========================================================
TOOLS = [
    # ---------------- DATABASE ----------------
    {"type": "function", "function": {
        "name": "get_active_goals",
        "description": "Get the user's currently active fitness goals.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_latest_measurement",
        "description": "Get the user's latest body measurement (weight, body fat, resting HR).",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_active_injuries",
        "description": "Get the user's currently active injuries.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_recent_workouts_db",
        "description": "Get the user's recent workouts stored in FitEdge's database.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Max workouts to return."}}},
    }},
    {"type": "function", "function": {
        "name": "get_user_fact",
        "description": "Get one stored fact about the user by key.",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string", "description": "The exact fact key."}},
            "required": ["key"]}},
    },
    {"type": "function", "function": {
        "name": "get_user_profile",
        "description": "Get the user's basic stored profile.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "create_goal",
        "description": "Create a fitness goal. Use only when the user explicitly asks to set a goal.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "target_date": {"type": "string", "description": "YYYY-MM-DD"}},
            "required": ["title"]}},
    },
    {"type": "function", "function": {
        "name": "create_measurement",
        "description": "Save a body measurement. Only include values the user actually gave.",
        "parameters": {"type": "object", "properties": {
            "weight": {"type": "number"},
            "body_fat": {"type": "number"},
            "resting_heart_rate": {"type": "number"},
            "notes": {"type": "string"}}},
    }},
    {"type": "function", "function": {
        "name": "create_injury",
        "description": "Record an injury reported by the user.",
        "parameters": {"type": "object", "properties": {
            "body_part": {"type": "string"},
            "description": {"type": "string"},
            "severity": {"type": "string"}},
            "required": ["body_part", "description"]}},
    },
    {"type": "function", "function": {
        "name": "create_fact",
        "description": "Store a long-term fact/preference/habit about the user (e.g. prefers morning workouts). Use when the user says remember/save/note something about themselves.",
        "parameters": {"type": "object", "properties": {
            "key": {"type": "string"},
            "value": {"type": "string"}},
            "required": ["key", "value"]}},
    },
    # ---------------- CALENDAR ----------------
    {"type": "function", "function": {
        "name": "get_calendar_events",
        "description": "Get upcoming calendar events.",
        "parameters": {"type": "object", "properties": {
            "days_ahead": {"type": "integer"},
            "max_results": {"type": "integer"}}},
    }},
    {"type": "function", "function": {
        "name": "add_calendar_event",
        "description": "Add an event to the user's calendar.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"},
            "date": {"type": "string", "description": "YYYY-MM-DD"},
            "start_time": {"type": "string", "description": "HH:MM 24-hour"},
            "duration_minutes": {"type": "integer"}},
            "required": ["title", "date", "start_time"]}},
    },
    # ---------------- EMAIL ----------------
    {"type": "function", "function": {
        "name": "draft_email",
        "description": "Draft an email without sending it.",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"]}},
    },
    {"type": "function", "function": {
        "name": "send_email",
        "description": "Send an email.",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"]}},
    },
    {"type": "function", "function": {
        "name": "read_recent_emails",
        "description": "Read recent emails.",
        "parameters": {"type": "object", "properties": {
            "max_results": {"type": "integer"}}},
    }},
    # ---------------- FITNESS (wger + intervals) ----------------
    {"type": "function", "function": {
        "name": "get_recent_workouts",
        "description": "Get recent strength workouts from wger.",
        "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}},
    }},
    {"type": "function", "function": {
        "name": "get_weight_log",
        "description": "Get recent bodyweight entries from wger.",
        "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}},
    }},
    {"type": "function", "function": {
        "name": "add_weight_entry",
        "description": "Add a bodyweight entry to wger.",
        "parameters": {"type": "object", "properties": {
            "weight": {"type": "number"},
            "entry_date": {"type": "string", "description": "YYYY-MM-DD"}},
            "required": ["weight"]}},
    },
    {"type": "function", "function": {
        "name": "get_recent_activities",
        "description": "Get recent cardio activities from Intervals.icu.",
        "parameters": {"type": "object", "properties": {
            "days_back": {"type": "integer"}, "limit": {"type": "integer"}}},
    }},
    {"type": "function", "function": {
        "name": "get_wellness",
        "description": "Get recent wellness data (HRV, resting HR, sleep) from Intervals.icu.",
        "parameters": {"type": "object", "properties": {"days_back": {"type": "integer"}}},
    }},
    {
    "type": "function",
    "function": {
        "name": "get_activity_details",
        "description": (
            "Get detailed data for one Intervals.icu activity. "
            "Identify the activity by title, date, or both. "
            "If multiple activities match, provide more specific information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "activity_title": {
                    "type": "string",
                    "description": "Activity title, for example 'Morning Run'.",
                },
                "activity_date": {
                    "type": "string",
                    "description": "Activity date in YYYY-MM-DD format.",
                },
            },
            "required": [],
        },
    },
        },
    # ---------------- WEATHER ----------------
    {"type": "function", "function": {
        "name": "get_current_weather",
        "description": "Get current weather. Coordinates default to the user's city if omitted.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"}}},
    }},
    {"type": "function", "function": {
        "name": "get_hourly_weather",
        "description": "Get hourly weather forecast. Coordinates default to the user's city if omitted.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"},
            "hours": {"type": "integer"}}},
    }},
    {"type": "function", "function": {
        "name": "get_daily_weather",
        "description": "Get daily weather forecast. Coordinates default to the user's city if omitted.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"},
            "days": {"type": "integer"}}},
    }},
    {
    "type": "function",
    "function": {
        "name": "run_pushup_session",
        "description": (
            "Start a live push-up session using the camera to count repetitions "
            "and evaluate push-up form. If the user specifies a number of push-ups, "
            "pass that number as target_reps. If no number is specified, omit target_reps."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "target_reps": {
                    "type": "integer",
                    "description": "The number of push-ups the user wants to do, if specified."
                }
            }
        }
    },
},
{
    "type": "function",
    "function": {
        "name": "analyze_food_image",
        "description": "Use the camera to analyze the user's food or plate and identify the foods present.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
},
{
    "type": "function",
    "function": {
        "name": "end_session",
        "description": "End the current FitEdge session when the user wants to log out, sign out, or indicates they are finished.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
},
]

# =========================================================
# TOOL GROUPS
# =========================================================
TOOL_GROUPS = {
    "database": [
        "get_active_goals", "get_latest_measurement", "get_active_injuries",
        "get_recent_workouts_db", "get_user_fact", "get_user_profile",
        "create_goal", "create_measurement", "create_injury", "create_fact",
    ],
    "calendar": ["get_calendar_events", "add_calendar_event"],
    "email": ["draft_email", "send_email", "read_recent_emails"],
    "fitness": [
        "get_recent_workouts", "get_weight_log", 
        "get_recent_activities", "get_wellness", "get_activity_details","create_goal"
    ],
    "weather": ["get_current_weather", "get_hourly_weather", "get_daily_weather"],
    "vision": ["run_pushup_session","analyze_food_image",],
    "session":["end_session"]
}

TOOL_MAP = {t["function"]["name"]: t for t in TOOLS}


def get_tools_for_groups(domains):
    """Collect the native tool definitions for ALL given domains (deduped)."""
    names = []
    for domain in domains:
        names.extend(TOOL_GROUPS.get(domain, []))
    seen = set()
    unique = [n for n in names if not (n in seen or seen.add(n))]
    return [TOOL_MAP[n] for n in unique if n in TOOL_MAP]


# =========================================================
# ROUTER  (returns a LIST of domains)
# =========================================================
ROUTER_PROMPT = """You are the FitEdge request router. Classify the user's request into ONE OR MORE domains. Return ONLY JSON, e.g. {"domains": ["database"]}.

Domains:
- database: the user's OWN stored data — their goals, measurements, weight, injuries, saved facts/preferences, profile — OR saving/remembering such data. ("What are my goals?", "remember I prefer mornings" -> database)
- fitness: reading stored workout/activity DATA from fitness services (past workouts, weight log, recent runs, wellness). NOT the user's goals/injuries/facts (those are database), and NOT starting an exercise session (that is vision).
- weather: weather, temperature, rain, or forecasts.
- calendar: calendar events or scheduling.
- email: reading, drafting, or sending email.
- vision: anything using the camera — analyzing food, checking exercise form, counting/monitoring push-ups, or STARTING a live exercise/workout/training session.
- session: ending the current FitEdge assistant session — logging out, signing out, saying goodbye, or indicating they are finished using FitEdge. NOT for workouts or exercises.
- none: general questions needing no personal data or service.

============================================================
CRITICAL RULE 1 — "WORKOUT" / "TRAIN" MEANS VISION
============================================================
"start a workout", "start training", "let's train", "let's start", "I want to work out", "I'm ready to exercise", "start my workout", "start the workout", "I think I should train now", "I want to train", "let's do pushups", "start a pushup session" all mean starting a LIVE CAMERA exercise SESSION -> use "vision", NOT "fitness".
The "fitness" domain is ONLY for reading stored workout/activity DATA (past workouts, weight log, recent runs). Never use "fitness" for starting or doing a workout.

============================================================
CRITICAL RULE 1B — FITNESS / WELLNESS VOCABULARY
============================================================
Use "fitness" for stored training and wellness data, including:
past workouts, recent runs, recent cardio, workout history,
activity history, HRV, resting heart rate, sleep, recovery,
training load, CTL, ATL, and similar fitness-service data.

============================================================
CRITICAL RULE 1C — PAST/PLANNED FITNESS DATA vs LIVE EXERCISE
============================================================
If the user asks what they did, what they have been doing,
their recent training, last workout, recent cardio, or activity
history -> "fitness".

If the user asks to START or PERFORM exercise now -> "vision".

Examples:
"what was my last workout?" -> ["fitness"]
"what have I been training lately?" -> ["fitness"]
"what's my next workout?" -> ["fitness"]
"what did I do last time?" -> ["fitness"]
"start my next workout" -> ["vision"]
"let's train now" -> ["vision"]
"watch me do pushups" -> ["vision"]


Examples:
"what's my HRV this week?" -> ["fitness"]
"what was my resting heart rate?" -> ["fitness"]
"how has my sleep been?" -> ["fitness"]
"what have I done for cardio lately?" -> ["fitness"]
"what did I do last time?" -> ["fitness"]
"what's my recent activity history?" -> ["fitness"]
"what was my last run?" -> ["fitness"]

"start a workout" or "do pushups" is still "vision", not "fitness".

============================================================
CRITICAL RULE 2 — "FITS MY GOALS" / "SUITABLE FOR ME" NEEDS DATABASE
============================================================
When the user asks whether something "fits my goals", "is good for my goals", "supports what I'm trying to achieve", "matches what I want", or "is suitable for me", that ALWAYS requires "database" (to check their goals) IN ADDITION to any other domain the request needs.
"scan my food and tell me if it fits my goals" -> ["vision", "database"]
"is this meal good for my goals?" -> ["vision", "database"]
"based on my goals, should I train outside today?" -> ["database", "weather"]
"find a workout time that fits what I'm trying to achieve" -> ["database", "calendar"]

============================================================
MEAL / FOOD EVALUATION
============================================================
When the user refers to a specific meal, food, or snack and asks
whether it is "okay", "good", or otherwise suitable to eat, treat
the specific food as requiring camera analysis ("vision").

If the question is about whether the food is okay FOR THE USER,
their goals, or what they are trying to achieve, also use
"database".

Examples:
"I just want to know if this meal is okay" -> ["vision", "database"]
"is this meal good for my goals?" -> ["vision", "database"]
"look at this snack and tell me if it's okay" -> ["vision", "database"]

A general food/nutrition question without a specific food being
shown does NOT require vision:
"what's a good protein source?" -> ["none"]
"how much protein is in chicken?" -> ["none"]

============================================================
EATING BEFORE TRAINING
============================================================
Do NOT add "database" just because the user asks whether they should
eat something before training.
"scan my food and tell me if I should eat it before running in this weather"
-> ["vision", "weather"]
"should I eat this before my run?" -> ["vision"]

============================================================
OUTDOOR TRAINING
============================================================
Training/running OUTSIDE + asking whether it is suitable/sensible
-> "weather".
"look at this snack and tell me if it's sensible before training outside today"
-> ["vision", "weather"]


============================================================
SESSION vs EXERCISE
============================================================
"session" means ending FitEdge, not exercising.
"about to run/train/exercise" -> "vision", not "session".
"I'm about to run, check the weather and scan what I'm eating"
-> ["weather", "vision"]
"I'm done with my workout" -> ["session"]

============================================================
CRITICAL RULE 3 — RECALLING WHAT THEY TOLD YOU IS DATABASE
============================================================
Asking to recall stored info — "what did I tell you about my goals?", "what was that goal I mentioned?", "what did I say I wanted?", "what did you save about me?" — is "database".

============================================================
CRITICAL RULE 3B — SAVING / RETAINING PREFERENCES
============================================================
Requests to remember, retain, or keep a personal preference/fact
must use "database", even when they do not explicitly say "remember"
or "save".

Examples:
"keep in mind that I prefer short workouts" -> ["database"]
"keep in mind that I prefer mornings" -> ["database"]
"remember that I prefer short workouts" -> ["database"]
"save that I prefer short workouts" -> ["database"]
"don't forget that I train in the morning" -> ["database"]

Do NOT use "fitness" merely because the saved preference concerns
training or workouts.


============================================================
CRITICAL RULE 4 — SESSION MEANS ENDING FITEDGE, NOT ENDING A WORKOUT
============================================================
Use "session" ONLY when the user is explicitly ending the current FitEdge assistant interaction.

Strong session signals include:
"log me out", "sign me out", "goodbye", "end the FitEdge session", "end this conversation", "stop using FitEdge", "close the session", "I'm leaving", or similarly explicit requests to stop using the assistant.

IMPORTANT:
Never use "session" just because the user says "done", "finished", "stop", "end", or "finish".
Those words may refer to a workout, exercise, task, or activity.

If the request contains a workout/exercise/training/run/push-up/activity context, DO NOT use "session" unless the user also explicitly says they want to log out, sign out, leave FitEdge, or end the assistant conversation.

Examples:
"I'm done" -> ["session"]
"I'm finished" -> ["session"]
"goodbye" -> ["session"]
"I'm done with my workout" -> ["none"]
"I finished training" -> ["none"]
"I finished my workout" -> ["none"]
"end my workout" -> ["none"]
"finish the workout" -> ["none"]
"stop my run" -> ["none"]
"stop the workout" -> ["none"]
"I'm done for today, but tell me my last workout before you sign me out" -> ["fitness", "session"]

The word "session" by itself does NOT mean the "session" domain.
Exercise sessions are handled by "vision".

============================================================
CRITICAL RULE 5 — MULTIPLE DOMAINS (compound requests)
============================================================
Many requests need MORE THAN ONE domain. You MUST include a domain for EVERY distinct action or topic. If actions are joined by "and", "then", "after", "before", or commas, return a domain for EACH one. Count the distinct things asked and include a domain for each — a request listing four things may need four domains. NEVER drop an action, and NEVER return "none" alongside real domains.

============================================================
CALENDAR read vs write
============================================================
- To ADD or SCHEDULE something, that is "calendar" (an add).
- To READ existing events, that is also "calendar".
Either way, scheduling or checking the calendar -> "calendar".

============================================================
WEATHER conditions
============================================================
Any mention of weather conditions — "if the weather is clear", "if it's sunny", "if it's not raining", "depending on the weather", "is it too hot", "will I need an umbrella" — ALWAYS requires "weather". Never drop weather when a weather condition is stated.


If the request refers to the user's recent training/cardio
AND asks whether future weather is suitable for that training,
include BOTH "fitness" and "weather".

Examples:
"what have I been doing lately and will tomorrow be good for a run?"
-> ["fitness", "weather"]

"is it cool enough tomorrow for the kind of training I've been doing?"
-> ["fitness", "weather"]

"what did I do last time and is tomorrow good for another run?"
-> ["fitness", "weather"]

"check my recent cardio and tell me if tomorrow looks good for a run"
-> ["fitness", "weather"]

IMPORTANT:
If the user explicitly requests another action before ending FitEdge,
include that action's domain AND "session".

Examples:
"check my calendar before I sign out" -> ["calendar", "session"]
"read my email then log me out" -> ["email", "session"]
"tell me my last workout before I sign out" -> ["fitness", "session"]
"check my goals and then goodbye" -> ["database", "session"]


============================================================
DO NOT trigger on incidental mentions
============================================================
If the user is only DEFINING or CASUALLY MENTIONING a word (not requesting the action), use "none".
"what does weather mean?" -> ["none"]
"I read something about weather today" -> ["none"]
"I was looking at my calendar" -> ["none"]
"my friend asked me about my goals" -> ["none"]
Negations also mean none: "don't check my calendar", "I don't need the weather" -> ["none"].

============================================================
EXAMPLES
============================================================
"what are my goals?" -> {"domains": ["database"]}
"what did I tell you about my goals?" -> {"domains": ["database"]}
"remember I prefer morning workouts" -> {"domains": ["database"]}
"what's the weather?" -> {"domains": ["weather"]}
"is it going to rain later?" -> {"domains": ["weather"]}
"do I have time tomorrow?" -> {"domains": ["calendar"]}
"scan my food" -> {"domains": ["vision"]}
"let's do pushups" -> {"domains": ["vision"]}
"I want to work out now" -> {"domains": ["vision"]}
"start the workout" -> {"domains": ["vision"]}
"start training" -> {"domains": ["vision"]}
"goodbye" -> {"domains": ["session"]}
"I'm done with my workout" -> {"domains": ["session"]}
"that's all for today" -> {"domains": ["session"]}
"what's a good protein source?" -> {"domains": ["none"]}
"explain progressive overload" -> {"domains": ["none"]}

Compound:
"what's the weather and what are my goals?" -> {"domains": ["weather", "database"]}
"scan my food and tell me if it fits my goals" -> {"domains": ["vision", "database"]}
"is this meal good for my goals?" -> {"domains": ["vision", "database"]}
"based on my goals, should I train outside today?" -> {"domains": ["database", "weather"]}
"check my goals then start a pushup session" -> {"domains": ["database", "vision"]}
"start pushups and then check my goals" -> {"domains": ["vision", "database"]}
"remember my goal and start a workout" -> {"domains": ["database", "vision"]}
"check my goals, tell me the weather, and start pushups" -> {"domains": ["database", "weather", "vision"]}
"tell me my goals, check tomorrow's weather, and start a pushup session" -> {"domains": ["database", "weather", "vision"]}
"check my schedule, check the weather, then start my workout" -> {"domains": ["calendar", "weather", "vision"]}
"check my goals, check my calendar, check the weather, then start pushups" -> {"domains": ["database", "calendar", "weather", "vision"]}
"I want to train tomorrow. Check my goals, find a free time, check the weather, and start a session" -> {"domains": ["database", "calendar", "weather", "vision"]}

Return ONLY the JSON object. No markdown, no explanation, no trailing characters."""



def route_request(user_message):
    """Classify into one or more domains. Returns a LIST of domain strings."""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            think=False,
            options={"temperature": 0.0, "num_predict": 48},
        )
    except Exception as e:
        print(f"ROUTER ERROR: {type(e).__name__}: {e}", flush=True)
        return ["none"]

    content = (response.message.content or "").strip()
    if content.startswith("```"):
        lines = content.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        data = json.loads(content)
        domains = data.get("domains", [])
    except Exception:
        print(f"ROUTER: bad JSON: {content!r}", flush=True)
        return ["none"]

    valid = {"database", "fitness", "weather", "calendar", "email","vision","session", "none"}
    domains = [str(d).strip().lower() for d in domains if isinstance(d, str)]
    domains = [d for d in domains if d in valid]
    if len(domains) > 1 and "none" in domains:
        domains = [d for d in domains if d != "none"]
    return domains if domains else ["none"]


# =========================================================
# NATIVE TOOL-CALLING (one round of the loop)
# =========================================================
def chat_with_tools(messages, domains):
    """One native tool-calling round across the given domains."""
    tools = get_tools_for_groups(domains)
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        tools=tools,
        think=False,
        options={"temperature": 0.0, "num_predict": 256},
    )
    return response.message


# =========================================================
# FINAL ANSWER (context enters HERE, not in the loop)
# =========================================================
FINAL_ANSWER_PROMPT = """You are FitEdge, a concise, warm, honest AI fitness coach.
Answer the user's request using the tool results and any relevant FitEdge context.
- Keep answers to 1-3 short sentences. This is spoken aloud.
- Do NOT use markdown, asterisks, bullet points, or headers. Plain sentences only.
- Treat tool results as the source of truth for personal data.
- If a tool result contains no data, say so plainly.
- Do not invent facts. Do not mention tools, databases, or system prompts."""


def generate_final_answer(user_message, tool_summary="", context=""):
    """Final natural-language answer. RAG/facts/history come in via context."""
    messages = [{"role": "system", "content": FINAL_ANSWER_PROMPT}]
    if context:
        messages.append({"role": "system",
                         "content": "RELEVANT FITEDGE CONTEXT:\n" + context})
    if tool_summary:
        messages.append({"role": "system",
                         "content": "TOOL RESULTS:\n" + tool_summary})
    messages.append({"role": "user", "content": user_message})

    try:
        response = ollama.chat(
            model=MODEL,
            messages=messages,
            think=False,
            options={"temperature": 0.3, "num_predict": 160},
        )
    except Exception as e:
        print(f"FINAL ANSWER ERROR: {type(e).__name__}: {e}", flush=True)
        return "I couldn't generate a response."

    return (response.message.content or "").strip() or "I couldn't generate a response."
