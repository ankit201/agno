from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-2.0-flash", grounding=True),
    add_datetime_to_instructions=True,
    markdown=True,
)
agent.print_response("What's the latest on Tariffs?", stream=True)
