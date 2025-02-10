"""
Tic Tac Toe Battle
---------------------------------
This example shows how to build a Tic Tac Toe game where two agents play against each other.

Usage Examples:
---------------

"""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat


def get_tic_tac_toe(
    debug_mode: bool = True,
) -> Agent:
    """
    Returns an instance of Tic Tac Toe Agent with integrated tools for playing the game.
    """

    tic_agent = Agent(
        name="Tic Agent",
        role="You are tic player of Tic Tac Toe. You'll have to make a move on the board. You'll make x's.",
        model=Claude(id="claude-3-5-sonnet-20241022"),
    )

    tac_agent = Agent(
        name="Tac Agent",
        role="You are tac player of Tic Tac Toe. You'll have to make a move on the board. You'll make o's.",
        model=OpenAIChat(id="gpt-4o"),
    )

    master_agent = Agent(
        name="Master Agent",
        role="You are a master of Tic Tac Toe. You'll have to oversee the game and make sure game is played correctly.",
        model=OpenAIChat(id="gpt-4o-mini"),
        team=[tic_agent, tac_agent],
        show_tool_calls=True,
        debug_mode=True,
        markdown=True,
    )

    return master_agent
