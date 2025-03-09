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
            logger.info(
                f"Establishing connection to MCP server: {server_params.command} {' '.join(server_params.args)}"
            )
            read, write = await client.__aenter__()
            logger.info("Connection established, creating client session")

            # Create the ClientSession with the connection
            session = ClientSession(read, write)

            # Initialize MCPTools with the session
            logger.info("Initializing MCPTools")
            mcp_tools = MCPTools(session=session)
            await mcp_tools.initialize()
            logger.info("MCPTools initialized successfully")

            return cls(client, session, mcp_tools)
        except Exception as e:
            # Ensure client is closed if initialization fails
            logger.error(f"Failed to create MCP connection: {e}")
            try:
                await client.__aexit__(type(e), e, None)
            except Exception as close_error:
                logger.error(
                    f"Error while closing client after failed initialization: {close_error}"
                )
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

        # Create a new event loop for initialization
        loop = asyncio.new_event_loop()
        try:
            # Run initialization in the new loop
            logger.info("Starting MCP manager initialization")
            loop.run_until_complete(self.initialize_mcp_manager())
            logger.info("MCP manager initialization completed")
        except asyncio.TimeoutError:
            logger.warning("MCP initialization timed out after 10 seconds")
        except Exception as e:
            logger.error(f"Error during MCP initialization: {e}")
        finally:
            loop.close()

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
        tasks = []
        for config in self.server_configs:
            # Check for required environment variables before creating tasks
            server_id = config.get("id")
            server_env_vars = config.get("env_vars", {})

            logger.info(f"Checking environment variables for server '{server_id}'")
            missing_vars = []
            for var_name, var_desc in server_env_vars.items():
                if not os.getenv(var_name):
                    missing_vars.append(f"{var_name} - {var_desc}")
                else:
                    # Log that we found the variable (without showing its value)
                    logger.info(f"Found environment variable: {var_name}")

            if missing_vars:
                logger.warning(
                    f"Skipping server '{server_id}' due to missing environment variables:\n"
                    + "\n".join(missing_vars)
                )
                continue

            # Only create tasks for servers with all required env vars
            logger.info(f"Creating connection task for server '{server_id}'")
            tasks.append(self.create_mcp_connection(config))

        if tasks:
            logger.info(f"Starting initialization of {len(tasks)} MCP servers")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Server {i + 1} initialization failed: {result}")
        else:
            logger.warning(
                "No MCP servers were initialized due to missing environment variables"
            )

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

        logger.info(f"Creating MCP connection for server '{server_id}'")
        # Create server parameters
        server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
        )

        # Create the MCPConnection
        try:
            logger.info(f"Attempting to connect to MCP server '{server_id}'")
            mcp_connection = await MCPConnection.create_mcp_connection(server_params)
            # Add the MCPConnection to the manager
            self.connections[server_id] = mcp_connection
            logger.info(f"Successfully connected to MCP server '{server_id}'")
            return mcp_connection
        except Exception as e:
            logger.error(
                f"Failed to create MCP connection for server '{server_id}': {e}"
            )
            raise

    def cleanup(self):
        """Clean up all MCP connections.

        This method can be called from both async and non-async contexts.
        """
        # Create a new event loop for cleanup if we're not in an async context
        if not asyncio.get_event_loop().is_running():
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(self._async_cleanup())
            finally:
                loop.close()
        else:
            # If we're already in an async context, create a task
            asyncio.create_task(self._async_cleanup())

        # Clear connections immediately
        self.connections.clear()

    async def _async_cleanup(self):
        """Internal async method to clean up all MCP connections."""
        if not self.connections:
            return

        cleanup_tasks = [
            connection.cleanup() for connection in self.connections.values()
        ]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)
