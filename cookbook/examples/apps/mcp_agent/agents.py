import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import Agent classes
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.models.groq import Groq
from agno.models.openai import OpenAIChat
from agno.storage.agent.sqlite import SqliteAgentStorage

# Import Agent instructions
from prompts import AGENT_DESCRIPTION, AGENT_INSTRUCTIONS, EXPECTED_OUTPUT_TEMPLATE

# ************* Setup Paths *************
# Define the current working directory
cwd = Path(__file__).parent
# Create an output directory for saving files
output_dir = cwd.joinpath("output")
output_dir.mkdir(parents=True, exist_ok=True)
# Create a tmp directory for storing agent sessions
tmp_dir = cwd.joinpath("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)
# *************************************

# ************* Agent Storage *************
# Configure SQLite storage for agent sessions
agent_storage = SqliteAgentStorage(
    table_name="mcp_agent_sessions",  # Table to store agent sessions
    db_file=str(tmp_dir.joinpath("agents.db")),  # SQLite database file
)
# *************************************


def get_mcp_agent(
    user_id: Optional[str] = None,
    model_str: str = "openai:gpt-4o",
    session_id: Optional[str] = None,
    num_history_responses: int = 5,
    debug_mode: bool = True,
) -> Agent:
    model = get_model_for_provider(model_str)

    return Agent(
        name="Universal MCP Agent",
        model=model,
        user_id=user_id,
        session_id=session_id,
        # Store Agent sessions in the database
        storage=agent_storage,
        # Agent description, instructions and expected output format
        description=AGENT_DESCRIPTION,
        instructions=AGENT_INSTRUCTIONS,
        expected_output=EXPECTED_OUTPUT_TEMPLATE,
        # Allow MCP Agent to read both chat history and tool call history for better context.
        read_chat_history=True,
        read_tool_call_history=True,
        # Append previous conversation responses into the new messages for context.
        add_history_to_messages=True,
        num_history_responses=num_history_responses,
        add_datetime_to_instructions=True,
        add_name_to_instructions=True,
        debug_mode=debug_mode,
        # Respond in markdown format
        markdown=True,
    )


def get_model_for_provider(model_str: str):
    """
    Creates and returns the appropriate model for a model string.

    Args:
        model_str: The model string (e.g., 'openai:gpt-4o', 'google:gemini-2.0-flash', 'anthropic:claude-3-5-sonnet', 'groq:llama-3.3-70b-versatile')

    Returns:
        An instance of the appropriate model class

    Raises:
        ValueError: If the provider is not supported
    """
    provider, model_name = model_str.split(":")
    if provider == "openai":
        return OpenAIChat(id=model_name)
    elif provider == "gemini":
        return Gemini(id=model_name)
    elif provider == "anthropic":
        if "thinking" in model_name:
            return Claude(
                id=model_name,
                max_tokens=16384,
                thinking={"type": "enabled", "budget_tokens": 8192},
            )
        return Claude(id=model_name, max_tokens=16384)
    elif provider == "groq":
        return Groq(id=model_name)
    else:
        raise ValueError(f"Unsupported model provider: {provider}")
