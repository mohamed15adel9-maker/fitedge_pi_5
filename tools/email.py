"""
tools/email.py

Gmail tools the LLM can call:
  - draft_email(to, subject, body)   creates a draft (safe: not sent)
  - send_email(to, subject, body)    sends an email
  - read_recent_emails(max_results)  reads recent inbox subjects/snippets

All return plain strings the LLM can read.

Uses the same Google auth as the calendar tool (auth/google_auth.py),
just building the "gmail" service instead of "calendar".
"""

import base64
from email.mime.text import MIMEText

from googleapiclient.discovery import build

from auth.google_auth import get_credentials   # see note below


def _get_gmail_service():
    """Builds an authenticated Gmail service using the shared credentials."""
    creds = get_credentials()
    return build("gmail", "v1", credentials=creds)


def _build_message(to, subject, body):
    """Creates a base64-encoded email message in the format Gmail expects."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}


def draft_email(to, subject, body):
    """
    Creates a DRAFT email (does not send). Safer default — lets the user
    review before sending.
    """
    try:
        service = _get_gmail_service()
        message = _build_message(to, subject, body)
        draft = service.users().drafts().create(
            userId="me", body={"message": message}
        ).execute()
        return (f"Draft created to {to} with subject '{subject}'. "
                f"Draft id: {draft.get('id', 'n/a')}. "
                f"The user can review and send it from Gmail.")
    except Exception as e:
        return f"ERROR creating draft: {e}"


def send_email(to, subject, body):
    """Sends an email immediately."""
    try:
        service = _get_gmail_service()
        message = _build_message(to, subject, body)
        sent = service.users().messages().send(
            userId="me", body=message
        ).execute()
        return (f"Email sent to {to} with subject '{subject}'. "
                f"Message id: {sent.get('id', 'n/a')}.")
    except Exception as e:
        return f"ERROR sending email: {e}"


def read_recent_emails(max_results=5):
    """Returns the sender, subject, and snippet of recent inbox messages."""
    try:
        service = _get_gmail_service()
        result = service.users().messages().list(
            userId="me", maxResults=max_results, labelIds=["INBOX"]
        ).execute()

        messages = result.get("messages", [])
        if not messages:
            return "No recent emails found."

        lines = []
        for msg in messages:
            full = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject"],
            ).execute()

            headers = full.get("payload", {}).get("headers", [])
            sender = next((h["value"] for h in headers if h["name"] == "From"), "?")
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "(no subject)")
            snippet = full.get("snippet", "")

            lines.append(f"From: {sender}\nSubject: {subject}\n{snippet}\n")

        return "\n".join(lines)
    except Exception as e:
        return f"ERROR reading emails: {e}"
