from memory.manager import get_all_facts, get_recent_messages
from brain.prompts import SYSTEM_PROMPT

USER_ID = 1
CONVERSATION_ID = "default"


def build_context():
    s = "START OF CONTEXT: "

    facts = get_all_facts(USER_ID)
    for fact in facts:
        s += fact["key"] + " " + str(fact["value"]) + " "

    msgs = get_recent_messages(CONVERSATION_ID, limit=10)
    for msg in msgs:
        s += str(msg["message"]) + " " + str(msg["timestamp"]) + " "

    return s


def build_prompt(user_message):
    return SYSTEM_PROMPT + build_context() + "END OF CONTEXT: " + user_message