import nest_asyncio
import streamlit as st
from agents import get_mcp_agent
from agno.agent import Agent
from agno.utils.log import logger
from utils import (
    about_widget,
    add_message,
    apply_theme,
    display_tool_calls,
    example_inputs,
    get_selected_model,
    session_selector_widget,
    utilities_widget,
)

nest_asyncio.apply()

apply_theme()


# # Define your server configurations
# server_configs = [
#     {
#         'id': 'github',
#         'command': 'npx',
#         'args': ['-y', '@modelcontextprotocol/server-github'],
#         'env_vars': {'GITHUB_TOKEN': 'GitHub Personal Access Token'}
#     },
#     # Add more server configs as needed
#     # {
#     #     'id': 'another-server',
#     #     'command': 'another-command',
#     #     'args': ['arg1', 'arg2'],
#     #     'env_vars': {'API_KEY': 'Description of API key'}
#     # }
# ]


def main() -> None:
    ####################################################################
    # App header
    ####################################################################
    st.markdown(
        "<h1 class='main-title'>Universal MCP Agent</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subtitle'>Interact with MCP servers using an AI Agent</p>",
        unsafe_allow_html=True,
    )

    ####################################################################
    # Settings
    ####################################################################
    selected_model = get_selected_model()
    # mcp_tools_list = initialize_mcp_tools(server_configs)

    ####################################################################
    # Initialize Agent
    ####################################################################
    try:
        if (
            "mcp_agent" not in st.session_state
            or st.session_state["mcp_agent"] is None
            or st.session_state.get("current_model") != selected_model
        ):
            logger.info("---*--- Creating new MCP Agent ---*---")
            mcp_agent = get_mcp_agent(model_str=selected_model)
            st.session_state["mcp_agent"] = mcp_agent
            st.session_state["current_model"] = selected_model
        else:
            mcp_agent = st.session_state["mcp_agent"]
    except Exception as e:
        st.error(f"Failed to initialize MCP Agent: {str(e)}")
        return

    ####################################################################
    # Load the current Agent session from the database
    ####################################################################
    try:
        st.session_state["mcp_agent_session_id"] = mcp_agent.load_session()
    except Exception as e:
        st.warning(
            f"Could not create Agent session: {str(e)}. Is the database running?"
        )
        return

    ####################################################################
    # Load agent runs (i.e. chat history) from memory
    ####################################################################
    load_agent_runs(mcp_agent)

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("✨ How can I help, bestie?"):
        add_message("user", prompt)

    ####################################################################
    # Show example inputs
    ####################################################################
    example_inputs()

    ####################################################################
    # Display agent messages
    ####################################################################
    display_agent_messages()

    ####################################################################
    # Generate response for user message
    ####################################################################
    process_last_message(mcp_agent)

    ####################################################################
    # Session selector
    ####################################################################
    session_selector_widget(mcp_agent, selected_model)

    ####################################################################
    # About section
    ####################################################################
    utilities_widget()
    about_widget()


def load_agent_runs(mcp_agent: Agent) -> None:
    """Load agent runs from agent memory."""
    # Load the agent runs
    agent_runs = mcp_agent.memory.runs
    if len(agent_runs) > 0:
        # If there are runs, load the messages
        logger.debug("Loading run history")
        st.session_state["messages"] = []
        # Loop through the runs and add the messages to the messages list
        for _run in agent_runs:
            if _run.message is not None:
                add_message(_run.message.role, _run.message.content)
            if _run.response is not None:
                add_message("assistant", _run.response.content, _run.response.tools)
    else:
        # If there are no runs, create an empty messages list
        logger.debug("No run history found")
        st.session_state["messages"] = []


def display_agent_messages() -> None:
    """Display previous messages."""
    for message in st.session_state["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    # Display tool calls if they exist in the message
                    if "tool_calls" in message and message["tool_calls"]:
                        display_tool_calls(st.empty(), message["tool_calls"])
                    st.markdown(_content)


def process_last_message(mcp_agent: Agent) -> None:
    """Process the last user message and generate a response."""
    last_message = (
        st.session_state["messages"][-1] if st.session_state["messages"] else None
    )
    if last_message and last_message.get("role") == "user":
        question = last_message["content"]
        with st.chat_message("assistant"):
            # Create container for tool calls
            tool_calls_container = st.empty()
            resp_container = st.empty()
            with st.spinner(":thinking_face: Thinking..."):
                response = ""
                try:
                    # Run the agent and stream the response
                    run_response = mcp_agent.run(question, stream=True)
                    for _resp_chunk in run_response:
                        # Display tool calls if available
                        if _resp_chunk.tools and len(_resp_chunk.tools) > 0:
                            display_tool_calls(tool_calls_container, _resp_chunk.tools)

                        # Display response
                        if _resp_chunk.content is not None:
                            response += _resp_chunk.content
                            resp_container.markdown(response)

                    add_message("assistant", response, mcp_agent.run_response.tools)
                except Exception as e:
                    logger.error(f"Error during agent run: {str(e)}", exc_info=True)
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    add_message("assistant", error_message)
                    st.error(error_message)


if __name__ == "__main__":
    main()
