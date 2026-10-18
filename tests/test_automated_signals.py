import pytest

from mail_assistant.automated_signals import detect_signals


def test_personal_email_has_no_signals(make_email):
    signals = detect_signals(make_email())

    assert not signals.no_reply_sender
    assert not signals.team_inbox_sender
    assert signals.ats_domain is None
    assert not signals.list_unsubscribe
    assert not signals.auto_submitted
    assert not signals.bulk_precedence


@pytest.mark.parametrize("local_part", ["noreply", "no-reply", "donotreply", "do-not-reply", "notifications"])
def test_no_reply_sender_is_detected(make_email, local_part):
    assert detect_signals(make_email(sender_address=f"{local_part}@foo.se")).no_reply_sender


@pytest.mark.parametrize("local_part", ["nora", "mailerlite.team", "anna.noreply.fan"])
def test_names_resembling_no_reply_are_not_detected(make_email, local_part):
    assert not detect_signals(make_email(sender_address=f"{local_part}@foo.se")).no_reply_sender


@pytest.mark.parametrize("local_part", ["careers", "jobs", "recruiting", "talent", "hr"])
def test_team_inbox_sender_is_detected(make_email, local_part):
    assert detect_signals(make_email(sender_address=f"{local_part}@foo.se")).team_inbox_sender


def test_hr_prefix_inside_a_name_is_not_a_team_inbox(make_email):
    assert not detect_signals(make_email(sender_address="hrishikesh@foo.se")).team_inbox_sender


def test_ats_domain_in_sender(make_email):
    signals = detect_signals(make_email(sender_address="no-reply@teamtailor-mail.com"))

    assert signals.ats_domain == "teamtailor-mail.com"
    assert signals.no_reply_sender


def test_ats_subdomain_matches(make_email):
    assert detect_signals(make_email(sender_address="anna@foo.teamtailor.com")).ats_domain == "teamtailor.com"


def test_ats_domain_found_in_reply_to(make_email):
    email = make_email(headers={"reply-to": "Foo AB <jobs@foo.teamtailor.com>"})

    assert detect_signals(email).ats_domain == "teamtailor.com"


def test_lookalike_domain_is_not_an_ats(make_email):
    assert detect_signals(make_email(sender_address="anna@notteamtailor.com")).ats_domain is None


def test_bulk_headers_are_detected(make_email):
    email = make_email(headers={
        "list-unsubscribe": "<https://foo.se/unsubscribe>",
        "auto-submitted": "auto-generated",
        "precedence": "Bulk",
    })
    signals = detect_signals(email)

    assert signals.list_unsubscribe
    assert signals.auto_submitted
    assert signals.bulk_precedence


def test_auto_submitted_no_means_written_by_a_person(make_email):
    assert not detect_signals(make_email(headers={"auto-submitted": "no"})).auto_submitted


def test_describe_lists_signals_as_yes_no(make_email):
    text = detect_signals(make_email(sender_address="no-reply@teamtailor-mail.com")).describe()

    assert "- no-reply sender address: yes" in text
    assert "- sent via applicant tracking system: teamtailor-mail.com" in text
    assert "- List-Unsubscribe header: no" in text
    assert "True" not in text and "False" not in text
