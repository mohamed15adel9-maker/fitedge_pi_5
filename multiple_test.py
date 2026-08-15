from memory.manager import add_message, get_recent_messages

# Add messages for two different users
add_message("default", "user", "Youssef message one", 1)
add_message("default", "assistant", "reply to Youssef", 1)
add_message("default", "user", "Michael message one", 2)
add_message("default", "assistant", "reply to Michael", 2)

# Each user should ONLY see their own
print("=== Youssef (1) history ===")
for m in get_recent_messages("default", 1, limit=10):
    print(m["role"], ":", m["message"])

print("=== Michael (2) history ===")
for m in get_recent_messages("default", 2, limit=10):
    print(m["role"], ":", m["message"])