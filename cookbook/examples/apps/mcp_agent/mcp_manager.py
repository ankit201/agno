import asyncio
import os
from typing import Any, Dict, List, Optional, Union

from agno.tools.mcp import MCPTools
from agno.utils.log import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPConnection:
    """Wrapper class for an MCP Server connection"""

    def __init__(self, client, session: ClientSession, mcp_tools: MCPTools):
        self.client = client
        self.session = session
        self.mcp_tools = mcp_tools

    @classmethod
    async def create_mcp_connection(
        cls, server_params: StdioServerParameters
    ) -> "MCPConnection":
        """Create an MCPConnection instance for given server parameters.
        Manually enters the stdio_client so that the session remains open.
        """
        # Create the stdio_client and manually enter its context to get the connection
        client = stdio_client(server_params)
        try:
            read, write = await client.__aenter__()

            # Create the ClientSession with the connection
            session = ClientSession(read, write)

            # Initialize MCPTools with the session
            mcp_tools = MCPTools(session=session)
            await mcp_tools.initialize()

            return cls(client, session, mcp_tools)
        except Exception as e:
            # Ensure client is closed if initialization fails
            await client.__aexit__(type(e), e, None)
            logger.error(f"Failed to create MCP connection: {e}")
            raise

    async def cleanup(self):
        """Clean up the active session and client. Call this to close the MCPConnection."""
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logger.error(f"Error closing session {self.session}: {e}")

        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
            except Exception as e:
                logger.error(f"Error closing client {self.client}: {e}")

        self.session = None
        self.client = None
        self.mcp_tools = None


class MCPManager:
    """Wrapper class to hold MCP Server connections"""

    def __init__(self, server_configs: List[Dict[str, Any]]):
        """Create an MCPManager that manages multiple MCP server configurations.

        Args:
            server_configs: List of dictionaries with server configurations.
                Each dictionary should have:
                - 'id': Id of MCP server (eg: 'github')
                - 'command': Command to run (eg: 'npx')
                - 'args': List of arguments (eg: ['-y', '@modelcontextprotocol/server-github'])
                - 'env_vars': Optional dict of environment variables required (eg: {'GITHUB_TOKEN': 'GitHub Personal Access Token'})
        """
        self.server_configs = server_configs
        self.connections: Dict[str, MCPConnection] = {}
        self._initialize_task = asyncio.create_task(self.initialize_mcp_manager())

    def get_mcp_tools(
        self, server_id: Optional[str] = None
    ) -> Union[MCPTools, List[MCPTools]]:
        """Get MCPTools instance(s) for a given server ID or all servers if no ID provided.

        Args:
            server_id: Optional ID of the server to get tools for. If None, returns tools for all servers.

        Returns:
            Either a single MCPTools instance or a list of all MCPTools instances.

        Raises:
            KeyError: If the specified server_id doesn't exist.
        """
        if server_id is None:
            return [connection.mcp_tools for connection in self.connections.values()]

        if server_id not in self.connections:
            raise KeyError(f"No MCP connection found for server ID: {server_id}")

        return self.connections[server_id].mcp_tools

    async def initialize_mcp_manager(self):
        """Initialize the MCPManager by creating MCPConnections for all server configurations."""
        tasks = [self.create_mcp_connection(config) for config in self.server_configs]
        await asyncio.gather(*tasks)

    async def create_mcp_connection(self, server_config: Dict[str, Any]):
        """Initialize an MCPConnection for a given server configuration."""
        server_id = server_config.get("id")
        if not server_id:
            raise ValueError("Server configuration missing required 'id' field")

        server_command = server_config.get("command")
        if not server_command:
            raise ValueError(
                f"Server configuration for '{server_id}' missing required 'command' field"
            )

        server_args = server_config.get("args", [])
        server_env_vars = server_config.get("env_vars", {})

        # Check for required environment variables
        if server_env_vars:
            missing_vars = []
            for var_name, var_desc in server_env_vars.items():
                if not os.getenv(var_name):
                    missing_vars.append(f"{var_name} - {var_desc}")

            if missing_vars:
                raise ValueError(
                    f"Missing environment variables for server '{server_id}':\n"
                    + "\n".join(missing_vars)
                )

        # Create server parameters
        server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
        )

        # Create the MCPConnection
        try:
            mcp_connection = await MCPConnection.create_mcp_connection(server_params)
            # Add the MCPConnection to the manager
            self.connections[server_id] = mcp_connection
        except Exception as e:
            logger.error(
                f"Failed to create MCP connection for server '{server_id}': {e}"
            )
            raise

    async def cleanup(self):
        """Clean up all MCP connections."""
        cleanup_tasks = [
            connection.cleanup() for connection in self.connections.values()
        ]
        await asyncio.gather(*cleanup_tasks)
        self.connections.clear()
