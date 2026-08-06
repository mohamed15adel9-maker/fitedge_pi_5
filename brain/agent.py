import json

from brain.llm import think            # must accept a messages list (see note below)
from tools.executor import run_tool    # your dispatcher: run_tool(name, args) -> result

MAX_ROUNDS = 5   # safety valve — never loop forever


def try_parse_tool_request(reply_text):
    """
    Decide whether the LLM's reply is a tool request or a final answer.
    Returns {"tool": ..., "args": {...}} if it's a tool request, else None.
    """
    try:
        data = json.loads(reply_text.strip())
    except (json.JSONDecodeError, ValueError):
        return None            # not JSON → it's a normal answer

    if isinstance(data, dict) and "tool" in data:
        # make sure there's always an args dict so callers can rely on it
        if "args" not in data or not isinstance(data["args"], dict):
            data["args"] = {}
        return data

    return None                # JSON but not a tool request → treat as answer


def run_agent(messages):
    """
    messages: a list like
        [{"role": "system", "content": ...},
         {"role": "user",   "content": ...}]
    Returns the final text answer (str).
    """
    for round_number in range(MAX_ROUNDS):

        # 1. Ask the LLM with the full conversation so far.
        reply = think(messages)

        # 2. Tool request or final answer?
        request = try_parse_tool_request(reply)

        # 3a. Normal answer → done.
        if request is None:
            return reply

        # 3b. It wants a tool → run it.
        tool_name = request["tool"]
        tool_args = request["args"]

        try:
            result = run_tool(tool_name, tool_args)
        except Exception as e:
            # If the tool fails, tell the LLM instead of crashing —
            # it gets another round to recover (e.g. fix a bad query).
            result = f"ERROR running tool '{tool_name}': {e}"

        # 4. Record what happened, so next round the LLM sees:
        #    - that it asked for a tool (its own request)
        #    - what the tool returned
        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Tool '{tool_name}' returned: {result}"
        })

        # loop continues → LLM now reasons with the new information

    # 5. Safety valve — too many rounds without a final answer.
    return "Sorry, I couldn't complete that request. Please try again."