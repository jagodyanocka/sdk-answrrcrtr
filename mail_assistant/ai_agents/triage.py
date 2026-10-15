from typing import Literal

from agents import Agent
from pydantic import BaseModel, Field

from mail_assistant.ai_agents import MODEL_NAME


class TriageResult(BaseModel):
    is_recruiter: bool = Field(description="True if this email is about a job application or job opportunity for me.")
    category: Literal["rejection", "interview_invite", "next_steps", "outreach", "other"]
    company: str | None = Field(description="Hiring company, if mentioned.")
    role: str | None = Field(description="Job title / position, if mentioned.")
    recruiter_name: str | None = Field(description="Name of the person who signed the email, if any.")
    summary: str = Field(description="One sentence describing what the email says.")


triage_agent = Agent(
    name="Triage Agent",
    instructions="""
You sort emails in a job seeker's inbox. Decide whether an email is from a recruiter, hiring manager,
talent/HR team or an applicant tracking system, and is about the job seeker's own application or a job
opportunity offered to them.

is_recruiter is false for: job-board alerts and newsletters (e.g. LinkedIn/Indeed job recommendations),
course or webinar marketing, and anything not about a specific application or opportunity.

Categories:
- rejection: the application will not move forward.
- interview_invite: asks to schedule or confirms an interview / call.
- next_steps: other progress in the process (assignment, offer, request for documents, status update).
- outreach: a recruiter proactively reaching out about a role.
- other: anything else (use this when is_recruiter is false).
""".strip(),
    model=MODEL_NAME,
    output_type=TriageResult,
)
