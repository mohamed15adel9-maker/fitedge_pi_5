from brain.agent import run_agent
from brain.prompts import SYSTEM_PROMPT

messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    {"role": "user", "content": "Schedule a run for me on August 15th at 7am."},
]
print(run_agent(messages))