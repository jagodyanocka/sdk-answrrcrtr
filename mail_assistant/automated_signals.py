import re
from dataclasses import dataclass
from email.utils import parseaddr

from mail_assistant.gmail_client import Email

ATS_DOMAINS = ["teamtailor-mail.com", "teamtailor.com"]

NO_REPLY_PATTERN = re.compile(r"^(no-?reply|do-?not-?reply|notifications?|mailer|automated?)\b")
# Shared team inboxes: weaker signal, real recruiters sometimes write from these too.
TEAM_INBOX_PATTERN = re.compile(r"^(careers?|jobs?|recruit(ing|ment)?|talent|hr|hiring|apply)\b")


@dataclass
class AutomationSignals:
    no_reply_sender: bool
    team_inbox_sender: bool
    ats_domain: str | None
    list_unsubscribe: bool
    auto_submitted: bool
    bulk_precedence: bool

    def describe(self) -> str:
        """Human/LLM-readable summary, passed to the automation agent."""
        def yes_no(value: bool) -> str:
            return "yes" if value else "no"

        return "\n".join([
            f"- no-reply sender address: {yes_no(self.no_reply_sender)}",
            f"- shared team inbox sender (careers@, jobs@, ...): {yes_no(self.team_inbox_sender)}",
            f"- sent via applicant tracking system: {self.ats_domain or 'no'}",
            f"- List-Unsubscribe header: {yes_no(self.list_unsubscribe)}",
            f"- Auto-Submitted header: {yes_no(self.auto_submitted)}",
            f"- Precedence bulk/list header: {yes_no(self.bulk_precedence)}",
        ])


def _address(header_value: str) -> str:
    return parseaddr(header_value)[1].lower()


def _find_ats_domain(addresses: list[str]) -> str | None:
    for address in addresses:
        domain = address.rpartition("@")[2]
        for ats in ATS_DOMAINS:
            if domain == ats or domain.endswith("." + ats):
                return ats
    return None


def detect_signals(email: Email) -> AutomationSignals:
    headers = email.headers
    local_part = email.sender_address.partition("@")[0]
    # ATS emails often use the company's name in From but the ATS domain in Reply-To or Return-Path.
    related_addresses = [
        email.sender_address,
        _address(headers.get("reply-to", "")),
        _address(headers.get("return-path", "")),
    ]
    return AutomationSignals(
        no_reply_sender=bool(NO_REPLY_PATTERN.match(local_part)),
        team_inbox_sender=bool(TEAM_INBOX_PATTERN.match(local_part)),
        ats_domain=_find_ats_domain([a for a in related_addresses if a]),
        list_unsubscribe="list-unsubscribe" in headers,
        auto_submitted=headers.get("auto-submitted", "no").strip().lower() != "no",
        bulk_precedence=headers.get("precedence", "").strip().lower() in ("bulk", "list", "junk"),
    )
