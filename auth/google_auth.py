"""
auth/google_auth.py

Handles Google OAuth for all Google tools (Calendar, Gmail).
get_credentials() does the login once and is shared by every tool.
On first run it opens a browser to approve; after that it reuses token.json.

If you ADD a scope (e.g. Gmail), delete auth/token.json so the next run
re-consents with the new permissions.
"""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

AUTH_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = AUTH_DIR / "credentials.json"
TOKEN_FILE = AUTH_DIR / "token.json"

# All permissions this app needs, across every tool.
SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_credentials():
    """
    Returns valid Google credentials, shared by all Google tools.
    Logs in via browser on first run, then reuses/refreshes token.json.
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return creds


def get_calendar_service():
    """Authenticated Google Calendar service."""
    return build("calendar", "v3", credentials=get_credentials())