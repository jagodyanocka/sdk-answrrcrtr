import base64

from mail_assistant.gmail_client import _to_email


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode()


def _gmail_message(payload: dict, headers: list[dict]) -> dict:
    """Minimal shape of what the Gmail API returns for messages.get(format="full")."""
    return {"id": "msg-1", "threadId": "thread-1", "payload": {**payload, "headers": headers}}


HEADERS = [
    {"name": "From", "value": "Anna Svensson <Anna.Svensson@Foo.se>"},
    {"name": "Subject", "value": "Din ansökan"},
    {"name": "Message-ID", "value": "<abc@foo.se>"},
    {"name": "List-Unsubscribe", "value": "<https://foo.se/u>"},
]


def test_headers_and_sender_are_parsed():
    email = _to_email(_gmail_message({"mimeType": "text/plain", "body": {"data": _b64("Hej")}}, HEADERS))

    assert email.sender_name == "Anna Svensson"
    assert email.sender_address == "anna.svensson@foo.se"
    assert email.subject == "Din ansökan"
    assert email.message_id == "<abc@foo.se>"
    assert email.thread_id == "thread-1"
    # Header names are lowercased so the signals code can look them up reliably.
    assert "list-unsubscribe" in email.headers


def test_plain_text_part_is_preferred_over_html():
    payload = {
        "mimeType": "multipart/alternative",
        "parts": [
            {"mimeType": "text/html", "body": {"data": _b64("<p>HTML version</p>")}},
            {"mimeType": "text/plain", "body": {"data": _b64("Plain version")}},
        ],
    }

    assert _to_email(_gmail_message(payload, HEADERS)).body == "Plain version"


def test_html_only_email_is_converted_to_text():
    html = "<style>p {color: red}</style><p>Hej &amp; tack</p><br>Mvh Anna"
    payload = {"mimeType": "text/html", "body": {"data": _b64(html)}}

    body = _to_email(_gmail_message(payload, HEADERS)).body

    assert "Hej & tack" in body
    assert "Mvh Anna" in body
    assert "<" not in body and "color" not in body


def test_body_is_found_in_nested_parts():
    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {"mimeType": "multipart/alternative", "parts": [
                {"mimeType": "text/plain", "body": {"data": _b64("Nested text")}},
            ]},
            {"mimeType": "application/pdf", "body": {"attachmentId": "att-1"}},
        ],
    }

    assert _to_email(_gmail_message(payload, HEADERS)).body == "Nested text"


def test_missing_from_header_does_not_crash():
    email = _to_email(_gmail_message({"mimeType": "text/plain", "body": {"data": _b64("x")}}, []))

    assert email.sender_address == ""
    assert email.subject == ""
