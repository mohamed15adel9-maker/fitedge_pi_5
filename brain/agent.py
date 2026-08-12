import json

from brain.llm import (
    think,
    generate_final_answer,
    generate_general_answer,
)

from tools.executor import run_tool

from build_context import build_context


MAX_ROUNDS = 3


# =========================================================
# TOOL REQUEST PARSER
# =========================================================

def try_parse_tool_request(reply_text):
    """
    Parse the JSON tool request returned by brain.llm.think().

    Expected:

    {
        "tool": "get_active_goals",
        "args": {}
    }
    """

    if not reply_text:
        return None

    text = reply_text.strip()

    try:
        data = json.loads(text)

    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict):
        return None

    if "tool" not in data:
        return None

    tool_name = data.get("tool")

    if not isinstance(tool_name, str):
        return None

    if not tool_name.strip():
        return None

    args = data.get("args", {})

    if not isinstance(args, dict):
        args = {}

    return {
        "tool": tool_name.strip(),
        "args": args,
    }


# =========================================================
# GET ORIGINAL USER MESSAGE
# =========================================================

def get_user_message(messages):
    """
    Extract the original user request.

    We intentionally ignore TOOL RESULT messages.
    """

    for message in reversed(messages):

        if not isinstance(message, dict):
            continue

        if message.get("role") != "user":
            continue

        content = message.get("content", "")

        if not content:
            continue

        if str(content).startswith("TOOL RESULT"):
            continue

        return str(content)

    return ""


# =========================================================
# AGENT
# =========================================================

def run_agent(messages):
    """
    Run the FitEdge agent.

    Architecture:

        User request
             ↓
        Qwen router
             ↓
        Domain
             ↓
        Minimal Qwen tool selection
             ↓
        Native tool call
             ↓
        Python executor
             ↓
        Tool result
             ↓
        Build rich context
             ├── RAG
             ├── user facts
             └── recent conversation
             ↓
        Qwen final answer
             ↓
        Return answer
    """

    # -----------------------------------------------------
    # GET ORIGINAL USER REQUEST
    # -----------------------------------------------------

    user_message = get_user_message(messages)

    if not user_message:

        print(
            "Agent: Could not find user message.",
            flush=True,
        )

        return "I couldn't determine what you are asking."

    print(
        f"Agent user request: {user_message}",
        flush=True,
    )

    # =====================================================
    # ROUND 1
    #
    # Router + native tool selection.
    #
    # IMPORTANT:
    # We DO NOT send RAG/facts/history here.
    # =====================================================

    print(
        "Agent round 1/3",
        flush=True,
    )

    try:

        reply, tool_group = think(
            [
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            tool_group=None,
        )

    except Exception as e:

        print(
            f"Agent error during tool selection: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return "I couldn't generate a response."

    if not reply:

        print(
            "Agent: Empty response from tool selector.",
            flush=True,
        )

        return "I couldn't generate a response."

    print(
        f"Agent tool group: {tool_group}",
        flush=True,
    )

    print(
        f"LLM tool-selection reply: {reply[:500]}",
        flush=True,
    )

    # =====================================================
    # NO TOOL REQUEST
    # =====================================================

    request = try_parse_tool_request(
        reply
    )

    if request is None:

        # -------------------------------------------------
        # If domain was "none", this is a normal question.
        #
        # Now we can safely build the rich context.
        # -------------------------------------------------

        print(
            "Agent: No tool request.",
            flush=True,
        )

        print(
            "Agent: Building context for final answer...",
            flush=True,
        )

        try:

            context = build_context(
                user_message
            )

        except Exception as e:

            print(
                f"Context error: "
                f"{type(e).__name__}: {e}",
                flush=True,
            )

            context = ""

        print(
            f"Agent: Context length: {len(context)}",
            flush=True,
        )

        # -------------------------------------------------
        # GENERAL ANSWER
        # -------------------------------------------------

        try:

            final_answer = generate_general_answer(
                user_message=user_message,
                context=context,
            )

        except Exception as e:

            print(
                f"Final answer error: "
                f"{type(e).__name__}: {e}",
                flush=True,
            )

            return "I couldn't generate a response."

        if not final_answer:

            return "I couldn't generate a response."

        print(
            "Agent: Final answer generated.",
            flush=True,
        )

        return final_answer

    # =====================================================
    # TOOL REQUEST
    # =====================================================

    tool_name = request["tool"]
    tool_args = request["args"]

    print(
        f"Agent requested tool: {tool_name}",
        flush=True,
    )

    print(
        f"Tool arguments: {tool_args}",
        flush=True,
    )

    # =====================================================
    # EXECUTE TOOL
    # =====================================================

    try:

        result = run_tool(
            tool_name,
            tool_args,
        )

    except Exception as e:

        result = {
            "success": False,
            "error": (
                f"{type(e).__name__}: {e}"
            ),
        }

    print(
        f"Tool result: {str(result)[:1000]}",
        flush=True,
    )

    # =====================================================
    # BUILD RICH CONTEXT
    #
    # THIS IS WHERE RAG NOW GOES.
    #
    # Tool selection has already finished.
    # =====================================================

    print(
        "Agent: Building rich final-answer context...",
        flush=True,
    )

    try:

        context = build_context(
            user_message
        )

    except Exception as e:

        print(
            f"Context error: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        context = ""

    print(
        f"Agent: Rich context length: "
        f"{len(context)}",
        flush=True,
    )

    # =====================================================
    # FINAL QWEN ANSWER
    # =====================================================

    print(
        "Agent: Sending tool result + context "
        "to final Qwen...",
        flush=True,
    )

    try:

        final_answer = generate_final_answer(
            user_message=user_message,
            tool_name=tool_name,
            tool_result=result,
            context=context,
        )

    except Exception as e:

        print(
            f"Final answer error: "
            f"{type(e).__name__}: {e}",
            flush=True,
        )

        return "I couldn't generate a response."

    # =====================================================
    # FINAL RESULT
    # =====================================================

    if not final_answer:

        return "I couldn't generate a response."

    print(
        "Agent: Final answer generated.",
        flush=True,
    )

    print(
        f"Final answer: {final_answer[:500]}",
        flush=True,
    )

    return final_answer