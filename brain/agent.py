"""
brain/agent.py

Hybrid agent:
  route → tool group → BOUNDED NATIVE TOOL LOOP → build_context → final answer

The loop feeds each tool result back to the model as a native role:"tool"
message, so the model can call another tool if genuinely needed, up to
MAX_ROUNDS. RAG/facts/history are added ONLY at the final-answer stage.
"""

from brain.llm import (
    route_request,
    chat_with_tools,
    generate_final_answer,
)
from tools.executor import run_tool
from build_context import build_context

MAX_ROUNDS = 5

# Single-user system: the DB tools operate on this user.
USER_ID = 1


def get_user_message(messages):
    """Extract the latest real user request (ignore tool-result messages)."""
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if content:
            return str(content)
    return ""


def run_agent(messages):
    user_message = get_user_message(messages)
    if not user_message:
        return "I couldn't determine what you are asking."

    print(f"Agent: user request -> {user_message}", flush=True)

    # -----------------------------------------------------
    # 1. ROUTE
    # -----------------------------------------------------
    domain = route_request(user_message)
    print(f"Agent: domain -> {domain}", flush=True)

    # -----------------------------------------------------
    # 2. "none" -> no tools, answer with context directly
    # -----------------------------------------------------
    if domain == "none":
        context = _safe_context(user_message)
        return generate_final_answer(user_message, tool_summary="", context=context)

    # -----------------------------------------------------
    # 3. BOUNDED NATIVE TOOL LOOP
    # -----------------------------------------------------
    loop_messages = [
        {"role": "system", "content":
            "Use tools to gather what you need. When done, stop calling tools."},
        {"role": "user", "content": user_message},
    ]
    tool_summaries = []

    for round_num in range(1, MAX_ROUNDS + 1):
        print(f"Agent: tool round {round_num}/{MAX_ROUNDS}", flush=True)

        reply = chat_with_tools(loop_messages, domain)

        # Append the assistant turn (may contain tool_calls) to the history.
        loop_messages.append({
            "role": "assistant",
            "content": reply.content or "",
            "tool_calls": reply.tool_calls or [],
        })

        # No tool calls -> the model is done gathering.
        if not reply.tool_calls:
            print("Agent: no more tool calls; exiting loop.", flush=True)
            break

        # Execute each requested tool and feed results back natively.
        for call in reply.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments or {})

            # Inject user_id for DB tools that need it.
            args = _inject_user_id(name, args)

            print(f"Agent: calling {name} args={args}", flush=True)
            try:
                result = run_tool(name, args)
            except Exception as e:
                result = f"ERROR: {type(e).__name__}: {e}"

            result_text = str(result)
            print(f"Agent: {name} -> {result_text[:300]}", flush=True)
            tool_summaries.append(f"{name}: {result_text}")

            loop_messages.append({
                "role": "tool",
                "content": result_text,
            })

    # -----------------------------------------------------
    # 4. BUILD CONTEXT (RAG + facts + history) — final stage only
    # -----------------------------------------------------
    context = _safe_context(user_message)

    # -----------------------------------------------------
    # 5. FINAL ANSWER
    # -----------------------------------------------------
    tool_summary = "\n".join(tool_summaries)
    return generate_final_answer(user_message, tool_summary=tool_summary, context=context)


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------
def _inject_user_id(name, args):
    """DB tools operate on the single user; add user_id if the tool needs it."""
    db_tools_needing_user = {
        "get_active_goals", "get_latest_measurement", "get_active_injuries",
        "get_recent_workouts_db", "get_user_fact", "get_user_profile",
        "create_goal", "create_measurement", "create_injury", "create_fact",
    }
    if name in db_tools_needing_user:
        args.setdefault("user_id", USER_ID)
    return args


def _safe_context(user_message):
    try:
        return build_context(user_message)
    except Exception as e:
        print(f"Agent: context error {type(e).__name__}: {e}", flush=True)
        return ""
