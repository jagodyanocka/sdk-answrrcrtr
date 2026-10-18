import pytest

from mail_assistant.gmail_client import Email


@pytest.fixture
def make_email():
    """Build a fake Email; tests only pass the fields they care about."""
    def _make(
        sender_address="anna.svensson@foo.se",
        sender_name="Anna Svensson",
        subject="Din ansökan",
        headers=None,
        body="Hej Jagoda,\nTack för samtalet i tisdags.\nMvh Anna",
    ) -> Email:
        return Email(
            id="msg-1",
            thread_id="thread-1",
            message_id="<msg-1@foo.se>",
            sender_name=sender_name,
            sender_address=sender_address,
            subject=subject,
            headers=headers or {},
            body=body,
        )

    return _make
