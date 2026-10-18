from agents import output_guardrail, Agent, GuardrailFunctionOutput, Runner
from pydantic import BaseModel, Field

from mail_assistant.ai_agents import MODEL_NAME

class EmailReviewOutputGuardrail(BaseModel):
    isProfessional: bool = Field(description="Whether the reply is professional")
    numberOfSentences: int = Field(description="The number of sentences in the reply")


reply_checker_agent = Agent(name="reply_checker_agent", instructions="You review agent written emails to recruiters", model=MODEL_NAME, output_type=EmailReviewOutputGuardrail)

@output_guardrail
async def check_email(ctx, agent, message) -> GuardrailFunctionOutput:
    check_result = await Runner.run(reply_checker_agent, f"Subject: {message.subject}\n\n{message.body}", context=ctx.context)
    review = check_result.final_output
    is_not_cool = not review.isProfessional
    return GuardrailFunctionOutput(output_info={"review": review}, tripwire_triggered=is_not_cool)
