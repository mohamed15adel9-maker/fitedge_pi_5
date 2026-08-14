"""
brain/llm.py

Hybrid FitEdge brain:
  - route_request(): classify into a domain (router)
  - tool groups: the model only sees the relevant domain's tools
  - native Ollama tool calling (no JSON round-trip)
  - a bounded multi-tool loop lives in agent.py and calls
    chat_with_tools() each round, feeding tool results back natively
  - build_context()/RAG/facts/history only at the final-answer stage
"""

import ollama

MODEL = "qwen3.5:2b"   # <-- set to whatever `ollama list` shows

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
        "description": "Get the user's latest body measurement (weight, body fat, resting HR, etc.).",
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
        "description": "Store a long-term fact about the user.",
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
        "description": "Get current weather. Requires latitude and longitude.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"}},
            "required": ["latitude", "longitude"]}},
    },
    {"type": "function", "function": {
        "name": "get_hourly_weather",
        "description": "Get hourly weather forecast.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"},
            "hours": {"type": "integer"}},
            "required": ["latitude", "longitude"]}},
    },
    {"type": "function", "function": {
        "name": "get_daily_weather",
        "description": "Get daily weather forecast.",
        "parameters": {"type": "object", "properties": {
            "latitude": {"type": "number"}, "longitude": {"type": "number"},
            "days": {"type": "integer"}},
            "required": ["latitude", "longitude"]}},
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
        "get_recent_workouts", "get_weight_log", "add_weight_entry",
        "get_recent_activities", "get_wellness", "get_activity_details",
    ],
    "weather": ["get_current_weather", "get_hourly_weather", "get_daily_weather"],
}

TOOL_MAP = {t["function"]["name"]: t for t in TOOLS}


def get_tools_for_group(domain):
    """Return the native tool definitions for one domain."""
    names = TOOL_GROUPS.get(domain, [])
    return [TOOL_MAP[n] for n in names if n in TOOL_MAP]


# =========================================================
# ROUTER
# =========================================================
ROUTER_PROMPT = """You are the FitEdge request router. Classify the user's request into EXACTLY ONE domain.

Domains:
- database: the user's own stored FitEdge data (goals, measurements, injuries, saved facts, profile) OR saving such data.
- fitness: workouts, activities, wellness/recovery, weight log from fitness services (wger, Intervals.icu).
- weather: weather or forecasts.
- calendar: calendar events, scheduling.
- email: reading, drafting, or sending email.
- none: general fitness questions needing no personal data or service (e.g. "what is progressive overload").

Return ONLY JSON: {"domain":"<one of the domains>"}
No markdown, no explanation."""


def route_request(user_message):
    """Classify the request into one domain. Returns the domain string."""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": user_message},
            ],
            think = False,
            options={"temperature": 0.0, "num_predict": 64},
        )
    except Exception as e:
        print(f"ROUTER ERROR: {type(e).__name__}: {e}", flush=True)
        return "none"

    content = (response.message.content or "").strip()
    if content.startswith("```"):
        lines = content.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    import json
    try:
        domain = json.loads(content).get("domain", "none")
    except Exception:
        return "none"

    domain = str(domain).strip().lower()
    valid = {"database", "fitness", "weather", "calendar", "email", "none"}
    return domain if domain in valid else "none"


# =========================================================
# TOOL-SELECTION PROMPT (used inside the loop)
# =========================================================
TOOL_LOOP_PROMPT = """You are FitEdge's tool-using agent.
Use the available tools to gather what you need to answer the user's request.
- Call a tool when the request needs personal data, an external service, or an action.
- You may call more than one tool across turns if genuinely needed.
- When you have enough information, STOP calling tools and reply with a short natural-language answer.
- Never invent tool arguments. Only use values the user provided.
- Do not explain the tool process to the user."""


# =========================================================
# NATIVE TOOL-CALLING (one round of the loop)
# =========================================================
def chat_with_tools(messages, domain):
    """
    One native tool-calling round.
    Returns the raw Ollama response.message object so agent.py can inspect
    .tool_calls (structured) and .content. NO JSON round-trip.
    """
    tools = get_tools_for_group(domain)
    response = ollama.chat(
        model=MODEL,
        messages=messages,
        tools=tools,
        think = False,
        options={"temperature": 0.0, "num_predict": 256},
    )
    return response.message


# =========================================================
# FINAL ANSWER (context enters HERE, not in the loop)
# =========================================================
FINAL_ANSWER_PROMPT = """You are FitEdge, a concise, warm, honest AI fitness coach.
Answer the user's request using the tool results and any relevant FitEdge context.
- Be concise and practical; suitable for voice output.
- Treat tool results as the source of truth for personal data.
- If a tool result contains no data, say so plainly.
- Do not invent facts. Do not mention tools, databases, or system prompts."""


def generate_final_answer(user_message, tool_summary="", context=""):
    """
    Final natural-language answer. RAG/facts/history come in via `context`.
    tool_summary is a plain-text digest of what the tools returned.
    """
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
            think = False,
            options={"temperature": 0.3, "num_predict": 256},
        )
    except Exception as e:
        print(f"FINAL ANSWER ERROR: {type(e).__name__}: {e}", flush=True)
        return "I couldn't generate a response."

    return (response.message.content or "").strip() or "I couldn't generate a response."
