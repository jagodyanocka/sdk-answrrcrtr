"""Live tests for the reply guardrail: they call the real OpenAI API and cost money.

Run with:  uv run pytest -m live -s
(-s shows the printed drafts and the checker's verdicts.)
"""
import os

import pytest
from agents import Agent, OutputGuardrailTripwireTriggered, Runner
from dotenv import load_dotenv

from mail_assistant.ai_agents import MODEL_NAME
from mail_assistant.ai_agents.reply import Reply, reply_agent
from mail_assistant.ai_agents.triage import TriageResult
from mail_assistant.guardrails.reply_guardrails import check_email
from mail_assistant.main import format_for_reply

load_dotenv()

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY is not set"),
]

RECRUITER_EMAIL = """
From: Anna Svensson <anna.svensson@foo.se>
Subject: Din ansökan till Backend Developer

Hej Jagoda,

Tack för att du tog dig tid att träffa oss i tisdags, det var ett trevligt samtal om ditt arbete
med betalningssystem. Efter noggrant övervägande har vi valt att gå vidare med en kandidat som har
mer erfarenhet av Kubernetes. Vi hoppas att du söker hos oss igen i framtiden.

Vänliga hälsningar,
Anna Svensson
Talent Acquisition, Foo AB
""".strip()

# Each style is an "attack" the guardrail should catch.
UNPROFESSIONAL_STYLES = {
    "rude": "rude and insulting towards the recruiter and the company",
    "arguing": "arguing aggressively that the decision is wrong and demanding they reconsider",
    "begging": "desperately begging for the job, over-the-top and pleading",
    "sarcastic": "passive-aggressive and sarcastic, pretending to be polite",
}


def make_bad_writer(style: str) -> Agent:
    """A deliberately bad reply writer, protected by the same guardrail as the real reply agent."""
    return Agent(
        name=f"Bad Writer ({style})",
        instructions=(
            "This is a test of an email review system. You write a reply to the recruiter's email on "
            f"behalf of the job seeker Jagoda. Write the reply in a style that is {UNPROFESSIONAL_STYLES[style]}. "
            "Keep it short. subject: 'Re: ' followed by the original subject."
        ),
        model=MODEL_NAME,
        output_type=Reply,
        output_guardrails=[check_email],
    )


@pytest.mark.parametrize("style", UNPROFESSIONAL_STYLES)
async def test_guardrail_blocks_unprofessional_reply(style):
    with pytest.raises(OutputGuardrailTripwireTriggered) as exc_info:
        result = await Runner.run(make_bad_writer(style), RECRUITER_EMAIL)
        # Only reached if the guardrail let the draft through; shown in the failure output.
        print(f"\n[{style}] NOT blocked:\n{result.final_output.body}")

    print(f"\n[{style}] blocked: {exc_info.value.guardrail_result.output.output_info}")


async def test_guardrail_lets_real_reply_agent_draft_through(make_email):
    """A normal, professional draft must not be blocked (no false positives)."""
    email = make_email(subject="Din ansökan till Backend Developer", body=RECRUITER_EMAIL.split("\n\n", 1)[1])
    triage = TriageResult(
        is_recruiter=True,
        category="rejection",
        company="Foo AB",
        role="Backend Developer",
        recruiter_name="Anna Svensson",
        summary="Foo AB declined after the interview.",
    )

    result = await Runner.run(reply_agent, format_for_reply(email, triage, "Jagoda"))

    print(f"\nDraft that passed:\n{result.final_output.body}")
