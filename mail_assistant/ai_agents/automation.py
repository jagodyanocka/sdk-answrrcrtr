from typing import Literal

from agents import Agent
from pydantic import Field, BaseModel

from mail_assistant.ai_agents import MODEL_NAME

class AutomationVerdict(BaseModel):
    is_automated: bool = Field(description="True if this email was generated automatically by a system or template.")
    confidence: Literal["low", "medium", "high"] = Field(description="Confidence level of the decision.")
    reasons: str = Field(description="Short, concrete reasons for the decision, pointing to signals and phrases relied on.")

automation_agent = Agent(
    name="Automation Agent",
    instructions="""
You decide whether a recruiting email was written personally by a human or generated automatically
(a template sent by an applicant tracking system or a bulk mailing). The job seeker only replies to
emails written by a real person. Replying to a no-reply robot is wasted effort, but ignoring a real
recruiter is worse, so when the evidence is mixed, lean towards "not automated" with low confidence.

Together with the email you get header signals that were computed in code:
- no-reply sender, Auto-Submitted, Precedence bulk/list and List-Unsubscribe are strong signs of automation.
- Sent via an applicant tracking system or from a shared inbox
  (careers@, jobs@) is only a weak sign: recruiters also write personal emails through these tools.

Signs of a template in the text:
- generic phrases such as "after careful consideration", "we have decided to move forward with other
  candidates", "we will keep your resume on file", "due to the high volume of applications",
  "thank you for applying".
- nothing specific about the candidate beyond their name and the job title (placeholder-style).
- signed by a team ("The Talent Acquisition Team", "Recruiting Team") or not signed at all.
- notes like "please do not reply to this email".

Signs of a human-written email:
- refers to specific conversations, interviews, people, dates or details of the candidate's profile.
- signed with a person's name, often with their job title or phone number.
- natural, individual wording; asks a question or invites a reply.

Give short, concrete reasons for your decision, pointing to the signals and phrases you relied on.
""".strip(),
    model=MODEL_NAME,
    output_type=AutomationVerdict
)