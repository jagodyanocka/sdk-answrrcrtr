import argparse
import asyncio

from agents import Runner, trace
from dotenv import load_dotenv

from mail_assistant.ai_agents.triage import TriageResult, triage_agent
from mail_assistant.gmail_client import Email, get_service, list_recent
from mail_assistant.automated_signals import detect_signals
from mail_assistant.ai_agents.automation import AutomationVerdict, automation_agent

load_dotenv()

# Keep model input (and cost) bounded; long email threads rarely need more than this.
MAX_BODY_CHARS = 4000
# How many emails are sent to the model at the same time.
CONCURRENCY = 5


def format_email(email: Email) -> str:
    return (
        f"From: {email.sender_name} <{email.sender_address}>\n"
        f"Subject: {email.subject}\n\n"
        f"{email.body[:MAX_BODY_CHARS]}"
    )


def format_for_automation(email: Email) -> str:
    signals = detect_signals(email)
    return (
        f"From: {email.sender_name} <{email.sender_address}>\n"
        f"Subject: {email.subject}\n\n"
        f"Header signals:\n{signals.describe()}\n\n"
        f"Body:\n{email.body[:MAX_BODY_CHARS]}"
    )


async def classify(email: Email, semaphore: asyncio.Semaphore) -> tuple[TriageResult, AutomationVerdict | None]:
    async with semaphore:
        triage = (await Runner.run(triage_agent, format_email(email))).final_output
        if not triage.is_recruiter:
            # Only recruiter emails go to the automation agent.
            return triage, None
        verdict = (await Runner.run(automation_agent, format_for_automation(email))).final_output
        return triage, verdict


async def main(days: int, max_results: int):
    service = get_service()
    query = f"in:inbox category:primary newer_than:{days}d -from:me"
    emails = await asyncio.to_thread(list_recent, service, query, max_results)
    print(f"Fetched {len(emails)} emails.\n")

    semaphore = asyncio.Semaphore(CONCURRENCY)
    with trace("Recruiter mail triage"):
        results = await asyncio.gather(*(classify(email, semaphore) for email in emails))

    for email, (r, verdict) in zip(emails, results):
        if verdict is None:
            marker = "-"
        else:
            marker = "AUTO" if verdict.is_automated else "HUMAN"
        print(f"{marker:<6} {r.category:<17} {r.company or '':<20.20} {email.subject:<50.50}")
        if verdict is not None:
            print(f"{'':<6} {r.summary}")
            print(f"{'':<6} [{verdict.confidence}] {verdict.reasons}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find recruiter emails in your Gmail inbox.")
    parser.add_argument("--days", type=int, default=7, help="How many days back to look.")
    parser.add_argument("--max", type=int, default=25, dest="max_results", help="Max emails to fetch.")
    args = parser.parse_args()
    asyncio.run(main(args.days, args.max_results))
