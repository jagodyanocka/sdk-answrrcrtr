import base64
import html
import re
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"

# Read-only for now; sending (step 5) will switch this to gmail.modify,
# which requires deleting token.json and logging in again.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class Email:
    id: str
    thread_id: str
    message_id: str
    sender_name: str
    sender_address: str
    subject: str
    headers: dict[str, str]
    body: str


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. Download the OAuth Desktop client JSON "
                    "from Google Cloud Console and save it there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def _decode(data: str) -> str:
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def _find_part(payload: dict, mime_type: str) -> str | None:
    if payload.get("mimeType") == mime_type and payload.get("body", {}).get("data"):
        return _decode(payload["body"]["data"])
    for part in payload.get("parts", []):
        found = _find_part(part, mime_type)
        if found:
            return found
    return None


def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", "", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>", "\n", raw)
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _extract_body(payload: dict) -> str:
    text = _find_part(payload, "text/plain")
    if text:
        return text.strip()
    raw_html = _find_part(payload, "text/html")
    return _html_to_text(raw_html) if raw_html else ""


def _to_email(msg: dict) -> Email:
    headers = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    name, address = parseaddr(headers.get("from", ""))
    return Email(
        id=msg["id"],
        thread_id=msg["threadId"],
        message_id=headers.get("message-id", ""),
        sender_name=name,
        sender_address=address.lower(),
        subject=headers.get("subject", ""),
        headers=headers,
        body=_extract_body(msg["payload"]),
    )


def list_recent(service, query: str, max_results: int = 25) -> list[Email]:
    response = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    emails = []
    for ref in response.get("messages", []):
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        emails.append(_to_email(msg))
    return emails


if __name__ == "__main__":
    service = get_service()
    for email in list_recent(service, query="in:inbox category:primary newer_than:7d -from:me", max_results=25):
        print(f"{email.sender_name or email.sender_address:<35.35} | {email.subject:<60.60} | {len(email.body)} chars")
