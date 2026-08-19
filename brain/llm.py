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
    {"type": "function", "function": {
        "name": "get_activity_details",
        "description": "Get splits/intervals for one activity by id.",
        "parameters": {"type": "object", "properties": {
            "activity_id": {"type": "string"}},
            "required": ["activity_id"]}},
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
- fitness: workouts, activities, recovery, or data from fitness services (NOT the user's goals/injuries/facts — those are database).
- weather: weather, temperature, rain, or forecasts.
- calendar: calendar events or scheduling.
- email: reading, drafting, or sending email.
- vision: requests that require camera-based visual analysis or live camera-based exercise monitoring, including analyzing food, identifying an exercise, checking exercise form, counting or monitoring push-ups or other exercises, or starting/performing an exercise session with the camera.
- session: requests to end the current FitEdge assistant session, including logging out, signing out, saying goodbye, saying they are done, or otherwise indicating that they want to stop using FitEdge. Do NOT use the session domain for workouts, exercises, push-ups, or other fitness activity sessions.
- none: general fitness questions needing no personal data or service.
 
CRITICAL — MULTIPLE DOMAINS:
A request often needs MORE THAN ONE domain. You MUST include EVERY domain the request touches. If the user asks about two different things joined by "and", return a domain for EACH part. Do NOT return just one domain when the request clearly covers two.
If the user explicitly wants to end the current FitEdge session — including phrases such as "log me out", "sign me out", "I am done", "I'm done", "that's all", "goodbye", "I'm finished", or similar expressions indicating that they want to stop using FitEdge — use the "session" domain. A workout or exercise session is NOT the "session" domain. If the request also requires another domain before ending, include every required domain.
 
Look for multiple topics: if the user mentions weather AND their goals, that is TWO domains. If they mention their goals AND their injuries, both are database. If they mention the weather AND scheduling, that is weather AND calendar.
 
- To ADD or SCHEDULE something on the calendar, use add_calendar_event, NOT get_calendar_events.
- get_calendar_events only READS existing events. To create a new event, you MUST call add_calendar_event.
- Do not repeatedly read the calendar. If the user wants to schedule something, add it.
 
 
  - Any mention of weather conditions — "if the weather is clear", "if it's sunny", "if it's not raining", "depending on the weather" — ALWAYS requires the "weather" domain. Never drop weather when a weather condition is stated. Examples: "schedule a run tomorrow if the weather is clear" -> {"domains": ["weather", "calendar"]} "book a workout for tomorrow if it's not raining" -> {"domains": ["weather", "calendar"]} "remind me to run tomorrow" -> {"domains": ["calendar"]} "what's the weather for my run?" -> {"domains": ["weather"]}
 
Examples:
"what are my goals?" -> {"domains": ["database"]}
"what's the weather?" -> {"domains": ["weather"]}
"what's the weather and what are my goals?" -> {"domains": ["weather", "database"]}
"what are my goals and my injuries?" -> {"domains": ["database"]}
"remember I prefer morning workouts" -> {"domains": ["database"]}
"schedule a run tomorrow if the weather is clear" -> {"domains": ["weather", "calendar"]}
"what's a good protein source?" -> {"domains": ["none"]}
"what's the weather and am I free tomorrow?" -> {"domains": ["weather", "calendar"]}
"what's on my plate?" -> {"domains": ["vision"]}
"analyze my food" -> {"domains": ["vision"]}
"check my exercise form" -> {"domains": ["vision"]}
"start a push-up session" -> {"domains": ["vision"]}
"let's do pushups" -> {"domains": ["vision"]}
"I am going to do pushups now" -> {"domains": ["vision"]}
"I'll do some pushups" -> {"domains": ["vision"]}
"watch me do pushups" -> {"domains": ["vision"]}
"count my pushups" -> {"domains": ["vision"]}
"goodbye" -> {"domains": ["session"]}
"that's all, goodbye" -> {"domains": ["session"]}
"log me out" -> {"domains": ["session"]}
"I am done" -> {"domains": ["session"]}
"check my goals and then start a push-up session" -> {"domains": ["database", "vision"]}
 
 
Return ONLY the JSON list. No markdown, no explanation."""


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
