
import json
import ollama


MODEL = "qwen3.5:2b"


TOOLS = [

    # =========================================================
    # DATABASE
    # =========================================================

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
            "description": "Get the user's latest body measurements including weight, body fat, waist, and resting heart rate.",
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
            "description": "Get the user's recent workouts stored in FitEdge's database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of workouts to return.",
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
                        "description": "The exact fact key to retrieve.",
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
            "description": "Get the user's basic stored profile information.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },


    # =========================================================
    # CALENDAR
    # =========================================================

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
                        "description": "Number of days to look ahead.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of events.",
                    },
                },
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "add_calendar_event",
            "description": "Add an event to the user's calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format.",
                    },
                    "start_time": {
                        "type": "string",
                        "description": "Time in HH:MM 24-hour format.",
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


    # =========================================================
    # EMAIL
    # =========================================================

    {
        "type": "function",
        "function": {
            "name": "draft_email",
            "description": "Draft an email without sending it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
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
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
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


    # =========================================================
    # WGER / STRENGTH
    # =========================================================

    {
        "type": "function",
        "function": {
            "name": "get_recent_workouts",
            "description": "Get the user's recent strength workouts from Wger.",
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
            "description": "Get the user's recent weight entries.",
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
                        "description": "Date in YYYY-MM-DD format.",
                    },
                },
                "required": ["weight", "entry_date"],
            },
        },
    },


    # =========================================================
    # CARDIO / RECOVERY
    # =========================================================

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
            "description": "Get recent wellness data such as HRV, resting heart rate and sleep.",
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
            "description": "Get detailed data for a specific cardio activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "activity_id": {
                        "type": "integer",
                    },
                },
                "required": ["activity_id"],
            },
        },
    },


    # =========================================================
    # WEATHER
    # =========================================================

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
                "required": ["latitude", "longitude"],
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
                "required": ["latitude", "longitude"],
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
                "required": ["latitude", "longitude"],
            },
        },
    },
]


def think(messages):
    """
    Send messages to Ollama.

    Ollama returns native tool calls in response.message.tool_calls.
    brain.agent.py currently expects a JSON string, so this function
    converts a native tool call into the JSON format expected by the agent.
    """

    try:
        print("LLM: Sending request to Ollama...", flush=True)

        response = ollama.chat(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            think=False,
            keep_alive="10m",
            options={
                "temperature": 0.2,
                "num_ctx": 2048,
                "num_predict": 80,
            },
        )

        print("LLM: Response received.", flush=True)

        # -----------------------------------------------------
        # Native Ollama tool call
        # -----------------------------------------------------

        if response.message.tool_calls:

            tool_call = response.message.tool_calls[0]

            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            print(
                f"LLM: Native tool call -> {tool_name}",
                flush=True
            )

            return json.dumps({
                "tool": tool_name,
                "args": tool_args,
            })

        # -----------------------------------------------------
        # Normal response
        # -----------------------------------------------------

        content = response.message.content

        if content:
            return content.strip()

        return ""

    except Exception as e:
        print(f"Error in think: {e}", flush=True)
        return None

