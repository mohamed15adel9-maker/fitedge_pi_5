# =========================================================
# IMPORTS
# =========================================================

import json
import ollama


# =========================================================
# MODEL
# =========================================================

MODEL = "qwen3.5:2b"


# =========================================================
# NATIVE OLLAMA TOOLS
# =========================================================

TOOLS = [

    # =====================================================
    # DATABASE
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "get_active_goals",
            "description": "Get the user's currently active fitness goals.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_latest_measurement",
            "description": (
                "Get the user's latest body measurements "
                "including weight, body fat, waist, and "
                "resting heart rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_active_injuries",
            "description": "Get the user's currently active injuries.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_recent_workouts_db",
            "description": (
                "Get the user's recent workouts stored "
                "in FitEdge's database."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": (
                            "Maximum number of workouts "
                            "to return."
                        ),
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_user_fact",
            "description": "Get one stored fact about the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": (
                            "The exact fact key to retrieve."
                        ),
                    },
                },
                "required": ["key"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": (
                "Get the user's basic stored "
                "profile information."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "create_user",
            "description": (
                "Create a new FitEdge user profile. "
                "Only use this when the user does not "
                "already have a profile."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "User's name.",
                    },
                    "age": {
                        "type": "integer",
                        "description": (
                            "User's age, if provided."
                        ),
                    },
                    "sex": {
                        "type": "string",
                        "description": (
                            "User's sex, if provided."
                        ),
                    },
                    "height": {
                        "type": "number",
                        "description": (
                            "User's height in centimeters, "
                            "if provided."
                        ),
                    },
                },
                "required": ["name"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "create_goal",
            "description": (
                "Create a new fitness goal. Use this "
                "when the user explicitly asks to create "
                "or set a goal."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short goal title.",
                    },
                    "description": {
                        "type": "string",
                        "description": (
                            "Detailed description of "
                            "the goal."
                        ),
                    },
                    "priority": {
                        "type": "integer",
                        "description": (
                            "Goal priority. Lower numbers "
                            "mean higher priority."
                        ),
                    },
                    "start_date": {
                        "type": "string",
                        "description": (
                            "Start date in YYYY-MM-DD format."
                        ),
                    },
                    "target_date": {
                        "type": "string",
                        "description": (
                            "Target completion date in "
                            "YYYY-MM-DD format."
                        ),
                    },
                },
                "required": ["title"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "create_measurement",
            "description": (
                "Save a new body measurement. Only include "
                "measurements the user actually provided."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": (
                            "Measurement date in "
                            "YYYY-MM-DD format."
                        ),
                    },
                    "weight": {
                        "type": "number",
                    },
                    "body_fat": {
                        "type": "number",
                    },
                    "waist": {
                        "type": "number",
                    },
                    "chest": {
                        "type": "number",
                    },
                    "hips": {
                        "type": "number",
                    },
                    "left_arm": {
                        "type": "number",
                    },
                    "right_arm": {
                        "type": "number",
                    },
                    "left_thigh": {
                        "type": "number",
                    },
                    "right_thigh": {
                        "type": "number",
                    },
                    "left_calf": {
                        "type": "number",
                    },
                    "right_calf": {
                        "type": "number",
                    },
                    "neck": {
                        "type": "number",
                    },
                    "resting_heart_rate": {
                        "type": "number",
                    },
                    "notes": {
                        "type": "string",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "create_injury",
            "description": "Record an injury reported by the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "body_part": {
                        "type": "string",
                    },
                    "description": {
                        "type": "string",
                    },
                    "severity": {
                        "type": "string",
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Injury date in "
                            "YYYY-MM-DD format."
                        ),
                    },
                    "active": {
                        "type": "boolean",
                        "description": (
                            "Whether the injury is "
                            "currently active."
                        ),
                    },
                },
                "required": [
                    "body_part",
                    "description",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "create_fact",
            "description": (
                "Store a long-term fact about the user "
                "that FitEdge should remember."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Short fact key.",
                    },
                    "value": {
                        "type": "string",
                        "description": "Fact value.",
                    },
                    "confidence": {
                        "type": "number",
                        "description": (
                            "Confidence from 0 to 1."
                        ),
                    },
                },
                "required": [
                    "key",
                    "value",
                ],
            },
        },
    },

    # =====================================================
    # CALENDAR
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get upcoming calendar events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_ahead": {
                        "type": "integer",
                        "description": (
                            "Number of days to look ahead."
                        ),
                    },
                    "max_results": {
                        "type": "integer",
                        "description": (
                            "Maximum number of events."
                        ),
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": (
                "Add an event to the user's calendar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                    },
                    "date": {
                        "type": "string",
                        "description": (
                            "Date in YYYY-MM-DD format."
                        ),
                    },
                    "start_time": {
                        "type": "string",
                        "description": (
                            "Time in HH:MM 24-hour format."
                        ),
                    },
                    "duration_minutes": {
                        "type": "integer",
                    },
                },
                "required": [
                    "title",
                    "date",
                    "start_time",
                ],
            },
        },
    },

    # =====================================================
    # EMAIL
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "Draft an email without sending it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                    },
                    "subject": {
                        "type": "string",
                    },
                    "body": {
                        "type": "string",
                    },
                },
                "required": [
                    "to",
                    "subject",
                    "body",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                    },
                    "subject": {
                        "type": "string",
                    },
                    "body": {
                        "type": "string",
                    },
                },
                "required": [
                    "to",
                    "subject",
                    "body",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "read_recent_emails",
            "description": "Read recent emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer",
                    },
                },
            },
        },
    },

    # =====================================================
    # WGER / STRENGTH
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "get_recent_workouts",
            "description": (
                "Get the user's recent strength "
                "workouts from Wger."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_weight_log",
            "description": (
                "Get the user's recent weight entries."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "add_weight_entry",
            "description": "Add a new weight entry for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weight": {
                        "type": "number",
                    },
                    "entry_date": {
                        "type": "string",
                        "description": (
                            "Date in YYYY-MM-DD format."
                        ),
                    },
                },
                "required": [
                    "weight",
                    "entry_date",
                ],
            },
        },
    },

    # =====================================================
    # CARDIO / RECOVERY
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "get_recent_activities",
            "description": "Get recent cardio activities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                    },
                    "limit": {
                        "type": "integer",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_wellness",
            "description": (
                "Get recent wellness data such as HRV, "
                "resting heart rate and sleep."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days_back": {
                        "type": "integer",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_activity_details",
            "description": (
                "Get detailed data for a specific "
                "cardio activity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer",
                    },
                },
                "required": [
                    "activity_id",
                ],
            },
        },
    },

    # =====================================================
    # WEATHER
    # =====================================================

    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get current weather conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                    },
                    "longitude": {
                        "type": "number",
                    },
                },
                "required": [
                    "latitude",
                    "longitude",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_hourly_weather",
            "description": "Get hourly weather forecast.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                    },
                    "longitude": {
                        "type": "number",
                    },
                    "hours": {
                        "type": "integer",
                    },
                },
                "required": [
                    "latitude",
                    "longitude",
                ],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "get_daily_weather",
            "description": "Get daily weather forecast.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                    },
                    "longitude": {
                        "type": "number",
                    },
                    "days": {
                        "type": "integer",
                    },
                },
                "required": [
                    "latitude",
                    "longitude",
                ],
            },
        },
    },
]


# =========================================================
# TOOL GROUPS
# =========================================================

TOOL_GROUPS = {
    "database": [
        "get_active_goals",
        "get_latest_measurement",
        "get_active_injuries",
        "get_recent_workouts_db",
        "get_user_fact",
        "get_user_profile",
        "create_user",
        "create_goal",
        "create_measurement",
        "create_injury",
        "create_fact",
    ],

    "calendar": [
        "get_calendar_events",
        "add_calendar_event",
    ],

    "email": [
        "draft_email",
        "send_email",
        "read_recent_emails",
    ],

    "fitness": [
        "get_recent_workouts",
        "get_weight_log",
        "add_weight_entry",
        "get_recent_activities",
        "get_wellness",
        "get_activity_details",
    ],

    "weather": [
        "get_current_weather",
        "get_hourly_weather",
        "get_daily_weather",
    ],
}


# =========================================================
# TOOL LOOKUP
# =========================================================

TOOL_MAP = {
    tool["function"]["name"]: tool
    for tool in TOOLS
}


def get_tools_for_group(tool_group):
    """
    Convert a selected domain into its actual
    Ollama native tool definitions.
    """

    tool_names = TOOL_GROUPS.get(
        tool_group,
        [],
    )

    return [
        TOOL_MAP[name]
        for name in tool_names
        if name in TOOL_MAP
    ]


# =========================================================
# ROUTER PROMPT
# =========================================================

ROUTER_PROMPT = """
You are the FitEdge request router.

Your ONLY job is to classify the user's request.

Choose exactly ONE domain:

database
fitness
weather
calendar
email
none

=========================================================
DATABASE
=========================================================

Use DATABASE for personal FitEdge data stored locally.

Examples:

"What are my active goals?"
"What are my goals?"
"Show me my goals."
"What is my latest weight?"
"What weight did I record?"
"What injuries do I have?"
"What injuries do I currently have?"
"Show me my FitEdge profile."
"What do you remember about me?"
"What facts have you saved?"
"Record my weight as 80 kg."
"Create a goal for me."
"Save this fact about me."

DATABASE means personal information stored by FitEdge.

=========================================================
FITNESS
=========================================================

Use FITNESS for workout, activity, wellness,
recovery, and fitness-service information.

Examples:

"Show me my recent workouts."
"What workouts did I do recently?"
"How active have I been?"
"How did I recover?"
"What is my wellness?"
"Show me my recent activities."
"Show me my weight log."

=========================================================
WEATHER
=========================================================

Use WEATHER for weather and forecasts.

Examples:

"What is the weather?"
"Will it rain tomorrow?"
"What will the weather be like this week?"

=========================================================
CALENDAR
=========================================================

Use CALENDAR for calendar events and scheduling.

Examples:

"What meetings do I have?"
"What is on my calendar?"
"Schedule a workout tomorrow."

=========================================================
EMAIL
=========================================================

Use EMAIL for reading, drafting, or sending emails.

Examples:

"Read my recent emails."
"Draft an email."
"Send an email."

=========================================================
NONE
=========================================================

Use NONE for general questions that do not require
personal FitEdge data or an external service.

Examples:

"What is progressive overload?"
"What is hypertrophy?"
"How does muscle growth work?"
"Explain creatine."

=========================================================
IMPORTANT
=========================================================

- Return ONLY valid JSON.
- Do NOT use Markdown.
- Do NOT use ```json.
- Do NOT explain your decision.
- Do NOT answer the user's question.
- Choose the domain based ONLY on the user's request.

Examples:

User:
"What are my active goals?"

Output:
{"domain":"database"}

User:
"What is my latest weight?"

Output:
{"domain":"database"}

User:
"Show me my recent workouts."

Output:
{"domain":"fitness"}

User:
"What will the weather be tomorrow?"

Output:
{"domain":"weather"}

User:
"What meetings do I have?"

Output:
{"domain":"calendar"}

User:
"Read my recent emails."

Output:
{"domain":"email"}

User:
"What is progressive overload?"

Output:
{"domain":"none"}
"""


# =========================================================
# ROUTER
# =========================================================

def route_request(user_message):
    """
    Route the user's request to one FitEdge domain.

    The router receives ONLY the user's request.

    It does NOT receive:
        - RAG
        - user facts
        - conversation history
        - tool definitions
    """

    print(
        "LLM ROUTER: Sending routing request...",
        flush=True,
    )

    messages = [
        {
            "role": "system",
            "content": ROUTER_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    try:

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.0,
                "num_ctx": 1024,
                "num_predict": 64,
            },
        )

    except Exception as e:

        print(
            f"LLM ROUTER ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return "none"

    content = (
        response.message.content or ""
    ).strip()

    print(
        "LLM ROUTER RESPONSE:",
        content,
        flush=True,
    )

    # =====================================================
    # CLEAN MARKDOWN CODE FENCES
    # =====================================================

    if content.startswith("```"):

        lines = content.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and lines[-1].strip() == "```"
        ):
            lines = lines[:-1]

        content = "\n".join(
            lines
        ).strip()

    # =====================================================
    # PARSE JSON
    # =====================================================

    try:

        data = json.loads(content)

    except (
        json.JSONDecodeError,
        ValueError,
    ):

        print(
            "LLM ROUTER: Invalid JSON after cleanup.",
            flush=True,
        )

        print(
            "LLM ROUTER CLEANED RESPONSE:",
            repr(content),
            flush=True,
        )

        return "none"

    if not isinstance(data, dict):

        print(
            "LLM ROUTER: Response is not a dictionary.",
            flush=True,
        )

        return "none"

    domain = data.get("domain")

    # =====================================================
    # NORMALIZE
    # =====================================================

    if isinstance(domain, str):

        domain = domain.strip().lower()

    # =====================================================
    # VALIDATE
    # =====================================================

    valid_domains = {
        "database",
        "fitness",
        "weather",
        "calendar",
        "email",
        "none",
    }

    if domain not in valid_domains:

        print(
            f"LLM ROUTER: Invalid domain: {domain}",
            flush=True,
        )

        return "none"

    print(
        f"LLM ROUTER: Selected domain -> {domain}",
        flush=True,
    )

    return domain


# =========================================================
# TOOL REQUEST
# =========================================================

def make_tool_request(response):
    """
    Convert Ollama's native tool call into the JSON format
    expected by brain.agent.
    """

    if not response.message.tool_calls:
        return None

    tool_call = response.message.tool_calls[0]

    tool_name = tool_call.function.name
    tool_args = tool_call.function.arguments

    print(
        f"LLM: Native tool call -> {tool_name}",
        flush=True,
    )

    return json.dumps({
        "tool": tool_name,
        "args": tool_args,
    })


# =========================================================
# EXTRACT USER REQUEST
# =========================================================

def extract_user_request(messages):
    """
    Extract the actual user request.

    Ignores:
        - system messages
        - tool-result messages
    """

    if not messages:
        return ""

    for message in reversed(messages):

        if not isinstance(message, dict):
            continue

        if message.get("role") != "user":
            continue

        content = message.get(
            "content",
            "",
        )

        if not content:
            continue

        content = str(content).strip()

        if not content:
            continue

        if content.startswith("TOOL RESULT"):
            continue

        return content

    return ""


# =========================================================
# TOOL-SELECTION PROMPT
# =========================================================

TOOL_SELECTION_PROMPT = """
You are FitEdge's tool-selection agent.

Your ONLY job is to select the correct available tool.

IMPORTANT:

- Use a tool whenever the user asks for personal FitEdge data.
- Use a tool whenever the user asks FitEdge to create, save,
  record, update, or retrieve personal data.
- Select the MOST appropriate available tool.
- ALWAYS use the native tool call.
- NEVER output the tool name as plain text.
- NEVER answer the user yourself.
- NEVER explain anything.
- NEVER say that you lack access.
- Do not invent information.
- Only use information explicitly provided by the user.
- If an argument is not provided by the user, do not invent it.

The available tools are the only tools you can use.

If the user asks:
"What are my active goals?"

and get_active_goals is available,

you MUST call:

get_active_goals

If the user asks:
"What is my latest weight?"

and get_latest_measurement is available,

you MUST call:

get_latest_measurement

If the user asks:
"What injuries do I currently have?"

and get_active_injuries is available,

you MUST call:

get_active_injuries

If the user asks:
"Show me my FitEdge profile."

and get_user_profile is available,

you MUST call:

get_user_profile

If the user asks:
"Create a goal for me to lose 5 kg."

and create_goal is available,

you MUST call:

create_goal

If the user asks:
"Record my weight as 80 kg."

and create_measurement is available,

you MUST call:

create_measurement
"""


# =========================================================
# SELECT TOOL
# =========================================================

def select_tool(
    user_message,
    tool_group,
):
    """
    Ask Qwen to select a native tool.

    NO:
        RAG
        user facts
        conversation history

    Only:
        system prompt
        user request
        selected domain tools
    """

    selected_tools = get_tools_for_group(
        tool_group
    )

    if not selected_tools:

        print(
            f"LLM: No tools available for "
            f"domain '{tool_group}'.",
            flush=True,
        )

        return None

    print(
        f"LLM: Selected {len(selected_tools)} tools "
        f"for domain '{tool_group}'.",
        flush=True,
    )

    print(
        "LLM: Tools -> "
        + ", ".join(
            tool["function"]["name"]
            for tool in selected_tools
        ),
        flush=True,
    )

    messages = [
        {
            "role": "system",
            "content": TOOL_SELECTION_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    print(
        "LLM: Sending minimal tool-selection prompt...",
        flush=True,
    )

    try:

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=selected_tools,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.0,
                "num_ctx": 2048,
                "num_predict": 128,
            },
        )

    except Exception as e:

        print(
            f"LLM TOOL SELECTION ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return None

    print(
        "LLM: Tool-selection response received.",
        flush=True,
    )

    print(
        f"LLM: Content -> "
        f"{repr(response.message.content)}",
        flush=True,
    )

    print(
        f"LLM: Tool calls -> "
        f"{response.message.tool_calls}",
        flush=True,
    )

    tool_request = make_tool_request(
        response
    )

    if tool_request:
        return tool_request

    if response.message.content:

        print(
            "LLM: Qwen returned text instead of "
            "a native tool call.",
            flush=True,
        )

    return None


# =========================================================
# FINAL ANSWER PROMPT
# =========================================================

FINAL_ANSWER_PROMPT = """
You are FitEdge, a concise AI fitness coach.

Answer the user's original request using the tool result
and any relevant FitEdge context.

IMPORTANT:

- Be concise.
- Be practical.
- Do not invent facts.
- Treat tool results as the source of truth for personal data.
- Do not mention internal tools.
- Do not mention databases.
- Do not mention prompts or system instructions.
- Do not claim information is unavailable if it exists
  in the tool result.
- If the tool result contains no data, say so clearly.
- Keep the response suitable for voice output.
"""


# =========================================================
# FINAL ANSWER
# =========================================================

def generate_final_answer(
    user_message,
    tool_name,
    tool_result,
    context="",
):
    """
    Generate the final natural-language answer.

    RAG, facts, and conversation context are allowed here.

    Tool selection has already finished.
    """

    final_messages = [
        {
            "role": "system",
            "content": FINAL_ANSWER_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    # =====================================================
    # FITEDGE CONTEXT / RAG
    # =====================================================

    if context:

        final_messages.append({
            "role": "system",
            "content": (
                "RELEVANT FITEDGE CONTEXT:\n"
                + context
            ),
        })

    # =====================================================
    # TOOL RESULT
    # =====================================================

    final_messages.append({
        "role": "tool",
        "content": (
            f"Tool: {tool_name}\n"
            f"Result: {tool_result}"
        ),
    })

    print(
        "LLM: Generating final answer...",
        flush=True,
    )

    try:

        response = ollama.chat(
            model=MODEL,
            messages=final_messages,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.2,
                "num_ctx": 4096,
                "num_predict": 256,
            },
        )

    except Exception as e:

        print(
            f"LLM FINAL ANSWER ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return "I couldn't generate a response."

    content = (
        response.message.content or ""
    ).strip()

    if not content:

        return "I couldn't generate a response."

    return content


# =========================================================
# GENERAL LLM ANSWER
# =========================================================

def generate_general_answer(
    user_message,
    context="",
):
    """
    Answer questions that do not require an external tool.

    RAG and user context are allowed here.
    """

    messages = [
        {
            "role": "system",
            "content": FINAL_ANSWER_PROMPT,
        },
    ]

    if context:

        messages.append({
            "role": "system",
            "content": (
                "RELEVANT FITEDGE CONTEXT:\n"
                + context
            ),
        })

    messages.append({
        "role": "user",
        "content": user_message,
    })

    print(
        "LLM: Generating general answer...",
        flush=True,
    )

    try:

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.2,
                "num_ctx": 4096,
                "num_predict": 256,
            },
        )

    except Exception as e:

        print(
            f"LLM GENERAL ANSWER ERROR: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return "I couldn't generate a response."

    content = (
        response.message.content or ""
    ).strip()

    if not content:

        return "I couldn't generate a response."

    return content


# =========================================================
# THINK
# =========================================================

def think(
    messages,
    tool_group=None,
    context="",
):
    """
    Run one FitEdge LLM stage.

    TOOL SELECTION:

        user request
             +
        minimal prompt
             +
        selected tools

    FINAL ANSWER:

        user request
             +
        tool result
             +
        RAG/facts/history context
    """

    try:

        # =================================================
        # EXTRACT USER REQUEST
        # =================================================

        user_message = extract_user_request(
            messages
        )

        if not user_message:

            print(
                "LLM: Could not extract user request.",
                flush=True,
            )

            return (
                "I couldn't determine what you are asking.",
                None,
            )

        # =================================================
        # ROUTING
        # =================================================

        if tool_group is None:

            tool_group = route_request(
                user_message
            )

        else:

            print(
                f"LLM: Reusing tool group -> "
                f"{tool_group}",
                flush=True,
            )

        print(
            f"LLM: Selected domain -> "
            f"{tool_group}",
            flush=True,
        )

        # =================================================
        # GENERAL QUESTION
        # =================================================

        if tool_group == "none":

            print(
                "LLM: No external tool required.",
                flush=True,
            )

            answer = generate_general_answer(
                user_message,
                context=context,
            )

            if not answer:

                answer = (
                    "I couldn't generate a response."
                )

            return (
                answer,
                "none",
            )

        # =================================================
        # TOOL SELECTION
        # =================================================

        tool_request = select_tool(
            user_message,
            tool_group,
        )

        if tool_request:

            return (
                tool_request,
                tool_group,
            )

        # =================================================
        # TOOL SELECTION FAILED
        # =================================================

        print(
            "LLM: No native tool call produced.",
            flush=True,
        )

        return (
            "",
            tool_group,
        )

    except Exception as e:

        print(
            f"Error in think: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return (
            "",
            tool_group,
        )