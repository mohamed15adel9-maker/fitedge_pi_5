import json
import requests

API_BASE = "https://intervals.icu/api/v1"

# Copy the same auth loading you already use.
from tools.intervals import _auth

activity_id = "19685239695"

resp = requests.get(
    f"{API_BASE}/activity/{activity_id}",
    params={"intervals": "true"},
    auth=_auth(),
    timeout=30,
)

print("STATUS:", resp.status_code)
print()
print("RAW RESPONSE:")
print(json.dumps(resp.json(), indent=2))