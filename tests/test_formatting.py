from mail_assistant.ai_agents.triage import TriageResult
from mail_assistant.main import MAX_BODY_CHARS, format_email, format_for_automation, format_for_reply


def _triage(**overrides) -> TriageResult:
    fields = dict(
        is_recruiter=True,
        category="rejection",
        company="Foo AB",
        role="Backend Developer",
        recruiter_name="Anna",
        summary="Foo AB declined the application.",
    )
    return TriageResult(**(fields | overrides))


def test_format_email_contains_sender_subject_and_body(make_email):
    text = format_email(make_email())

    assert "From: Anna Svensson <anna.svensson@foo.se>" in text
    assert "Subject: Din ansökan" in text
    assert "Tack för samtalet i tisdags." in text


def test_long_body_is_cut(make_email):
    text = format_email(make_email(body="x" * (MAX_BODY_CHARS + 500)))

    assert text.count("x") == MAX_BODY_CHARS


def test_format_for_automation_includes_signals(make_email):
    text = format_for_automation(make_email(sender_address="no-reply@teamtailor-mail.com"))

    assert "Header signals:" in text
    assert "- no-reply sender address: yes" in text
    assert "Body:" in text


def test_format_for_reply_contains_facts_email_and_name(make_email):
    text = format_for_reply(make_email(), _triage(), "Jagoda")

    assert "Category: rejection" in text
    assert "Company: Foo AB" in text
    assert "Recruiter name: Anna" in text
    assert "Tack för samtalet i tisdags." in text
    assert "Jagoda" in text


def test_format_for_reply_never_shows_none(make_email):
    text = format_for_reply(make_email(), _triage(company=None, role=None, recruiter_name=None), "Jagoda")

    assert "None" not in text
    assert "Company: unknown" in text


def test_job_seeker_name_is_on_its_own_line(make_email):
    # Regression: the name used to be glued onto the last line of the email body.
    text = format_for_reply(make_email(), _triage(), "Jagoda")

    assert "Job seeker's name: Jagoda" in text.splitlines()
