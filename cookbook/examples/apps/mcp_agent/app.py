import nest_asyncio
import streamlit as st
from agents import get_mcp_agent
from agno.agent import Agent
from agno.utils.log import logger
from utils import (
    CUSTOM_CSS,
    about_widget,
    add_message,
    display_tool_calls,
    get_selected_model,
    rename_session_widget,
    session_selector_widget,
    utilities_widget,
)

nest_asyncio.apply()

# Page configuration
st.set_page_config(
    page_title="Universal MCP Agent",
    page_icon=":crystal_ball:",
    layout="wide",
)

# Load custom CSS with dark mode support
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def main() -> None:
    ####################################################################
    # App header
    ####################################################################
    st.markdown(
        "<h1 class='main-title'>Universal MCP Agent</h1>", unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subtitle'>Interact with any MCP server using an AI Agent</p>",
        unsafe_allow_html=True,
    )

    ####################################################################
    # Settings
    ####################################################################
    selected_model = get_selected_model()

    ####################################################################
    # Initialize Agent
    ####################################################################
    mcp_agent: Agent
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

    ####################################################################
    # Load the current Agent session from the database
    ####################################################################
    try:
        st.session_state["mcp_agent_session_id"] = mcp_agent.load_session()
    except Exception:
        st.warning("Could not create Agent session, is the database running?")
        return

    ####################################################################
    # Load runs from memory
    ####################################################################
    agent_runs = mcp_agent.memory.runs
    if len(agent_runs) > 0:
        logger.debug("Loading run history")
        st.session_state["messages"] = []
        # Loop through the runs and add the messages to the messages list
        for _run in agent_runs:
            if _run.message is not None:
                add_message(_run.message.role, _run.message.content)
            if _run.response is not None:
                add_message("assistant", _run.response.content, _run.response.tools)
    else:
        logger.debug("No run history found")
        st.session_state["messages"] = []

    ####################################################################
    # Get user input
    ####################################################################
    if prompt := st.chat_input("✨ How can I help, bestie?"):
        add_message("user", prompt)

    ####################################################################
    # Display chat history
    ####################################################################
    for message in st.session_state["messages"]:
        if message["role"] in ["user", "assistant"]:
            _content = message["content"]
            if _content is not None:
                with st.chat_message(message["role"]):
                    # Display tool calls if they exist in the message
                    if "tool_calls" in message and message["tool_calls"]:
                        display_tool_calls(st.empty(), message["tool_calls"])
                    st.markdown(_content)

    ####################################################################
    # Generate response for user message
    # - Get the last message from the messages list
    # - If the last message is a user message, run the agent
    ####################################################################
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
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    add_message("assistant", error_message)
                    st.error(error_message)

    ####################################################################
    # Session selector
    ####################################################################
    session_selector_widget(mcp_agent, selected_model)
    rename_session_widget(mcp_agent)

    ####################################################################
    # About section
    ####################################################################
    utilities_widget()
    about_widget()


if __name__ == "__main__":
    main()
