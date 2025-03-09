import asyncio
import os
from typing import Any, Dict, List, Optional

import streamlit as st
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import StdioClient

# Global storage for active clients and sessions to prevent garbage collection
_active_clients = {}
_active_sessions = {}


@st.cache_resource
def initialize_mcp_tools(server_configs: List[Dict[str, Any]]) -> List[MCPTools]:
    """
    Initialize multiple MCP servers and return their respective MCPTools objects.

    Args:
        server_configs: List of dictionaries with server configurations.
            Each dictionary should have:
            - 'id': Unique identifier for this server
            - 'command': Command to run (e.g., 'npx')
            - 'args': List of arguments
            - 'env_vars': Optional dict of environment variables required

    Returns:
        List of initialized MCPTools objects
    """
    return asyncio.run(_initialize_mcp_tools_async(server_configs))


async def _initialize_mcp_tools_async(
    server_configs: List[Dict[str, Any]],
) -> List[MCPTools]:
    """Async implementation of initialize_mcp_tools"""
    tools = []

    for config in server_configs:
        server_id = config["id"]

        # Check for required environment variables
        if "env_vars" in config:
            for var_name, var_desc in config["env_vars"].items():
                if not os.getenv(var_name):
                    raise ValueError(
                        f"Missing environment variable: {var_name} - {var_desc}"
                    )

        # Create server parameters
        server_params = StdioServerParameters(
            command=config["command"],
            args=config["args"],
        )

        # Create client manually without context manager
        client = StdioClient(server_params)
        await client.start()
        read, write = client.reader, client.writer

        # Create session manually without context manager
        session = ClientSession(read, write)
        await session.initialize()

        # Initialize MCP toolkit
        mcp_tools = MCPTools(session=session)
        await mcp_tools.initialize()

        # Store references to prevent garbage collection
        _active_clients[server_id] = client
        _active_sessions[server_id] = session

        tools.append(mcp_tools)

    return tools


async def cleanup_mcp_tools():
    """Clean up all active sessions and clients. Call this when you're done."""
    for session_id, session in _active_sessions.items():
        try:
            await session.close()
        except Exception as e:
            print(f"Error closing session {session_id}: {e}")

    for client_id, client in _active_clients.items():
        try:
            await client.close()
        except Exception as e:
            print(f"Error closing client {client_id}: {e}")

    _active_sessions.clear()
    _active_clients.clear()
