
import json

from brain.llm import think
from tools.executor import run_tool


MAX_ROUNDS = 3


def try_parse_tool_request(reply_text):
    """
    Parse the JSON tool request returned by brain.llm.think().

    Expected format:

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

    if not isinstance(tool_name, str) or not tool_name.strip():
        return None

    args = data.get("args", {})

    if not isinstance(args, dict):
        args = {}

    return {
        "tool": tool_name.strip(),
        "args": args,
    }


def run_agent(messages):
    """
    Run the FitEdge agent.

    brain.llm.think() returns a string:

    Normal answer:
        "You don't have any active goals."

    Tool request:
        {"tool":"get_active_goals","args":{}}

    The agent executes the tool and sends the result
    back to the LLM for the final answer.
    """

    for round_number in range(MAX_ROUNDS):

        print(
            f"Agent round {round_number + 1}/{MAX_ROUNDS}",
            flush=True,
        )

        # -----------------------------------------------------
        # ASK LLM
        # -----------------------------------------------------

        reply = think(messages)

        if not reply:
            return "I couldn't generate a response."

        print(
            f"LLM reply: {reply[:500]}",
            flush=True,
        )

        # -----------------------------------------------------
        # CHECK FOR TOOL REQUEST
        # -----------------------------------------------------

        request = try_parse_tool_request(reply)

        # -----------------------------------------------------
        # NORMAL ANSWER
        # -----------------------------------------------------

        if request is None:

            print(
                "Agent produced final answer.",
                flush=True,
            )

            return reply.strip()

        # -----------------------------------------------------
        # TOOL REQUEST
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # EXECUTE TOOL
        # -----------------------------------------------------

        try:

            result = run_tool(
                tool_name,
                tool_args,
            )

        except Exception as e:

            result = (
                f"ERROR running tool '{tool_name}': "
                f"{type(e).__name__}: {e}"
            )

        print(
            f"Tool result: {str(result)[:500]}",
            flush=True,
        )

        # -----------------------------------------------------
        # SEND TOOL RESULT BACK TO LLM
        # -----------------------------------------------------

        # The LLM originally requested the tool.
        messages.append({
            "role": "assistant",
            "content": reply,
        })

        # Give the tool result to the LLM.
        messages.append({
            "role": "user",
            "content": (
                f"TOOL RESULT\n"
                f"Tool: {tool_name}\n"
                f"Result: {result}\n\n"
                f"Use this result to answer the user's original request."
            ),
        })

        # Continue to next round.
        # The LLM should now produce the final answer.

    # ---------------------------------------------------------
    # MAX ROUNDS
    # ---------------------------------------------------------

    print(
        "Agent stopped: maximum tool rounds reached.",
        flush=True,
    )

    return (
        "I couldn't complete the request within "
        "the allowed number of tool calls."
    )

