#
# from dotenv import load_dotenv
# from agents import Agent, Runner, trace, function_tool, ModelSettings
# import asyncio
#
#
# load_dotenv()
# MODEL_NAME = "gpt-5.4-mini"
#
# intro = """
# You are a sales agent working for ComplAI,
# a company that provides a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI.
# You write emails.
# """
#
# instructions1 = intro + "Your email style is professional, serious, with gravitas and credibility."
# instructions2 = intro + "Your email style is witty, engaging, and humorous."
# instructions3 = intro + "Your email style is concise, to the point, in the style of a busy senior executive."
#
# sales_agent1 = Agent(name="Professional Sales Agent", instructions=instructions1, model=MODEL_NAME)
# sales_agent2 = Agent(name="Humorous Sales Agent", instructions=instructions2, model=MODEL_NAME)
# sales_agent3 = Agent(name="Executive Sales Agent", instructions=instructions3, model=MODEL_NAME)
#
# @function_tool
# def send_email_tool(subject: str, text_body: str, html_body: str) -> str:
#     """
#         Send out an email with the given subject and body to all sales prospects
#
#         Args:
#             subject: The subject of the email
#             text_body: The body of the email as plain text
#             html_body: The HTML body of the email
#         """
#     print(subject, text_body, html_body)
#     return "Email printed"
#
# decision = """
# You pick the best cold sales email from the given options.
# Imagine you are a customer and pick the one you are most likely to respond to.
# Do not give an explanation; reply with the selected email only.
# """
# required_tools = ModelSettings(tool_choice="required")
# sales_agent_manager = Agent(name="Sales Agent Manager", instructions=decision, model=MODEL_NAME, tools=[send_email_tool], model_settings=required_tools)
#
# async def main():
#     message = "Write a cold sales email"
#     with trace("Parallel cold emails"):
#         results = await asyncio.gather(
#             Runner.run(sales_agent1, message),
#             Runner.run(sales_agent2, message),
#             Runner.run(sales_agent3, message),
#         )
#     outputs = [result.final_output for result in results]
#     emails = "cold emails:\n\n" + "\n\nEmail:\n\n".join(outputs)
#     best = await Runner.run(sales_agent_manager, emails)
#     print(f"Best sales email:\n\n{best.final_output}")
#
#
# if __name__ == "__main__":
#     asyncio.run(main())