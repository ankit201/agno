import nest_asyncio
import streamlit as st
from agents import get_mcp_agent
from agno.agent import Agent
from agno.utils.log import logger
from mcp_manager import MCPManager
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


def initialize_mcp_manager():
    """Initialize the MCP Manager with server configurations if not already in session state."""
    if "mcp_manager" not in st.session_state:
        # Define server configurations
        server_configs = [
            {
                "id": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env_vars": {"GITHUB_TOKEN": "GitHub Personal Access Token"},
                "description": "GitHub MCP Server - Access GitHub repositories and issues",
            },
            {
                "id": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env_vars": {},
                "description": "Filesystem MCP Server - Access local files and directories",
            },
            # Add more server configurations as needed
        ]

        try:
            logger.info("Initializing MCP Manager")
            st.session_state["mcp_manager"] = MCPManager(server_configs)
            logger.info("MCP Manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize MCP Manager: {e}")
            st.error(f"Failed to initialize MCP Manager: {str(e)}")
            st.session_state["mcp_manager"] = None


def get_available_mcp_servers():
    """Get list of available MCP servers from the manager."""
    if "mcp_manager" in st.session_state and st.session_state["mcp_manager"]:
        return list(st.session_state["mcp_manager"].connections.keys())
    return []


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
    # Initialize MCP Manager
    ####################################################################
    initialize_mcp_manager()

    ####################################################################
    # Settings
    ####################################################################
    col1, col2 = st.columns([1, 1])

    with col1:
        selected_model = get_selected_model()

    with col2:
        # MCP Server selection
        available_servers = get_available_mcp_servers()
        if available_servers:
            selected_server = st.selectbox(
                "Select MCP Server",
                options=["All Servers"] + available_servers,
                index=0,
                help="Choose which MCP server to use for this conversation",
            )
            st.session_state["selected_mcp_server"] = (
                None if selected_server == "All Servers" else selected_server
            )
        else:
            st.warning(
                "No MCP servers available. Check your environment variables and server configurations."
            )
            st.session_state["selected_mcp_server"] = None

    ####################################################################
    # Initialize Agent
    ####################################################################
    try:
        if (
            "mcp_agent" not in st.session_state
            or st.session_state["mcp_agent"] is None
            or st.session_state.get("current_model") != selected_model
            or st.session_state.get("current_mcp_server")
            != st.session_state.get("selected_mcp_server")
        ):
            logger.info("---*--- Creating new MCP Agent ---*---")

            # Get MCP tools based on selection
            mcp_tools = None
            if "mcp_manager" in st.session_state and st.session_state["mcp_manager"]:
                try:
                    selected_server = st.session_state.get("selected_mcp_server")
                    mcp_tools = st.session_state["mcp_manager"].get_mcp_tools(
                        selected_server
                    )
                    logger.info(
                        f"Using MCP tools for server: {selected_server if selected_server else 'All'}"
                    )
                except KeyError as e:
                    logger.warning(f"Could not get MCP tools: {e}")

            mcp_agent = get_mcp_agent(model_str=selected_model, mcp_tools=mcp_tools)
            st.session_state["mcp_agent"] = mcp_agent
            st.session_state["current_model"] = selected_model
            st.session_state["current_mcp_server"] = st.session_state.get(
                "selected_mcp_server"
            )
        else:
            mcp_agent = st.session_state["mcp_agent"]
    except Exception as e:
        st.error(f"Failed to initialize MCP Agent: {str(e)}")
        return

    # Display active MCP server info
    if st.session_state.get("current_mcp_server"):
        st.info(f"Active MCP Server: {st.session_state.get('current_mcp_server')}")
    elif available_servers:
        st.info("Using all available MCP servers")

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
