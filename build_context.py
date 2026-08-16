from memory.manager import get_all_facts, get_recent_messages
from brain.prompts import system_prompt
from rag.retrieval import retrieve


#USER_ID = 1
CONVERSATION_ID = "default"

MAX_HISTORY_MESSAGES = 4


def build_context(user_message,user_id):
    parts = []

    # ---------------------------------------------------------
    # RAG knowledge
    # ---------------------------------------------------------

    knowledge = retrieve(user_message)

    if knowledge and not knowledge.startswith("No relevant"):
        parts.append(
            "RELEVANT KNOWLEDGE:\n" + knowledge
        )

    # ---------------------------------------------------------
    # User facts
    # ---------------------------------------------------------

    facts = get_all_facts(user_id)

    if facts:
        fact_text = "\n".join(
            f"{fact['key']}: {fact['value']}"
            for fact in facts
        )

        parts.append(
            "USER FACTS:\n" + fact_text
        )

    # ---------------------------------------------------------
    # Recent conversation
    # ---------------------------------------------------------

    msgs = get_recent_messages(
        CONVERSATION_ID,
        user_id,
        limit=MAX_HISTORY_MESSAGES
    )

    if msgs:
        history_text = "\n".join(
            f"{msg['role']}: {msg['message']}"
            for msg in msgs
        )

        parts.append(
            "RECENT CONVERSATION:\n" + history_text
        )

    return "\n\n".join(parts)


def build_prompt(user_message,user_id):
    """
    Build Ollama-compatible chat messages.

    Returns a list of dictionaries instead of one giant string.
    """

    context = build_context(user_message,user_id)

    system_content = system_prompt()

    if context:
        system_content += "\n\n" + context

    return [
        {
            "role": "system",
            "content": system_content,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]