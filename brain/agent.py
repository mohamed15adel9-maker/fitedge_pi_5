"""
brain/agent.py

Hybrid agent with MULTI-DOMAIN routing:
  route (-> list of domains) -> BOUNDED NATIVE TOOL LOOP -> build_context -> final answer

The loop feeds each tool result back to the model as a native role:"tool"
message, so the model can call another tool if genuinely needed, up to
MAX_ROUNDS. RAG/facts/history are added ONLY at the final-answer stage.

user_id is passed in (multi-user): it flows main -> run_agent -> run_tool.
"""

from brain.llm import (
    route_request,
    chat_with_tools,
    generate_final_answer,
)
from tools.executor import run_tool
from build_context import build_context

MAX_ROUNDS = 5


def get_user_message(messages):
    """Extract the latest real user request."""
    for message in reversed(messages):
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if content:
            return str(content)
    return ""


def run_agent(messages, user_id):
    display_data_used = False
    display_text = None
    display_type = None

    user_message = get_user_message(messages)
    if not user_message:
        return "I couldn't determine what you are asking."

    print(f"Agent: user request -> {user_message}", flush=True)

    # -----------------------------------------------------
    # 1. ROUTE  (returns a LIST of domains)
    # -----------------------------------------------------
    domains = route_request(user_message)
    print(f"Agent: domains -> {domains}", flush=True)

    # -----------------------------------------------------
    # 2. "none" only -> no tools, answer with context directly
    # -----------------------------------------------------
    if domains == ["none"]:
        context = _safe_context(user_message, user_id)
        return generate_final_answer(
            user_message,
            tool_summary="",
            context=context,
        ), False,None,None

    # -----------------------------------------------------
    # 3. BOUNDED NATIVE TOOL LOOP (across all routed domains)
    # -----------------------------------------------------
    loop_messages = [
        {
            "role": "system",
            "content":
                "Use tools to gather what you need. For multi-step requests, gather "
                "all needed information first, then act. When done, stop calling tools.",
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]

    tool_summaries = []

    for round_num in range(1, MAX_ROUNDS + 1):
        print(
            f"Agent: tool round {round_num}/{MAX_ROUNDS}",
            flush=True,
        )

        reply = chat_with_tools(loop_messages, domains)

        loop_messages.append({
            "role": "assistant",
            "content": reply.content or "",
            "tool_calls": reply.tool_calls or [],
        })

        if not reply.tool_calls:
            print(
                "Agent: no more tool calls; exiting loop.",
                flush=True,
            )
            break

        for call in reply.tool_calls:
            name = call.function.name
            args = dict(call.function.arguments or {})

            print(
                f"Agent: calling {name} args={args}",
                flush=True,
            )

            try:
                result = run_tool(
                    name,
                    args,
                    user_id,
                )
            except Exception as e:
                result = f"ERROR: {type(e).__name__}: {e}"

            # -------------------------------------------------
            # Check whether this tool returned display data
            # -------------------------------------------------
            if isinstance(result, dict) and "result" in result:
                result_text = str(result["result"])

                if result.get("display_data", False):
                    display_data_used = True
                    display_text = str(result["result"])
                    display_type = result.get("display_type")

            else:
                result_text = str(result)

            print(
                f"Agent: {name} -> {result_text[:300]}",
                flush=True,
            )

            tool_summaries.append(
                f"{name}: {result_text}"
            )

            loop_messages.append({
                "role": "tool",
                "content": result_text,
            })

    # -----------------------------------------------------
    # 4. BUILD CONTEXT (RAG + facts + history) - final stage only
    # -----------------------------------------------------
    context = _safe_context(
        user_message,
        user_id,
    )

    # -----------------------------------------------------
    # 5. FINAL ANSWER
    # -----------------------------------------------------
    tool_summary = "\n".join(tool_summaries)

    return generate_final_answer(
        user_message,
        tool_summary=tool_summary,
        context=context,
    ), display_data_used,display_text,display_type


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------
def _safe_context(user_message, user_id):
    try:
        return build_context(
            user_message,
            user_id,
        )
    except Exception as e:
        print(
            f"Agent: context error {type(e).__name__}: {e}",
            flush=True,
        )
        return ""