import asyncio
import os
from typing import Dict, List, Optional

from agno.tools.mcp import MCPTools
from agno.utils.log import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    id: str = Field(..., description="ID of the MCP server (e.g., 'github')")
    command: str = Field(..., description="Command to run (e.g., 'npx')")
    args: List[str] = Field(
        default_factory=list, description="List of command arguments"
    )
    env_vars: List[str] = Field(
        default_factory=list,
        description="List of required environment variables (e.g., ['GITHUB_TOKEN'])",
    )


mcp_server_configs = {
    "github": MCPServerConfig(
        id="github",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env_vars=["GITHUB_TOKEN"],
    ),
    "filesystem": MCPServerConfig(
        id="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "."],
    ),
    "git": MCPServerConfig(
        id="git",
        command="uvx",
        args=["mcp-server-git"],
    ),
    "brave-search": MCPServerConfig(
        id="brave-search",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env_vars=["BRAVE_API_KEY"],
    ),
}


class MCPManager:
    """Manager for Model Context Protocol (MCP) server connections."""

    def __init__(self, server_ids: List[str]):
        """Create an MCPManager that manages multiple MCP server connections.

        Args:
            server_ids: List of server IDs to initialize (must exist in mcp_server_configs).
        """
        self.server_ids = server_ids
        self.server_configs = []
        for server_id in server_ids:
            if server_id not in mcp_server_configs:
                raise ValueError(
                    f"Unknown server ID: {server_id}. Available servers: {', '.join(mcp_server_configs.keys())}"
                )
            self.server_configs.append(mcp_server_configs[server_id])
        self.mcp_tools_map: Dict[str, MCPTools] = {}
        self._initialized = False

    @classmethod
    async def create(cls, server_ids: List[str]) -> "MCPManager":
        """Factory method to create and initialize an MCPManager.

        Args:
            server_ids: List of server IDs to initialize.

        Returns:
            An initialized MCPManager instance.
        """
        manager = cls(server_ids)
        await manager.initialize()
        return manager

    @classmethod
    def create_sync(cls, server_ids: List[str]) -> "MCPManager":
        """Synchronous factory method to create and initialize an MCPManager.

        Args:
            server_ids: List of server IDs to initialize.

        Returns:
            An initialized MCPManager instance.
        """
        manager = cls(server_ids)

        # Run initialization in a new event loop
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            loop.run_until_complete(manager.initialize())
        finally:
            loop.close()

        return manager

    async def initialize(self):
        """Asynchronously initialize the MCP manager.

        This method should be called after creating the MCPManager instance.
        """
        if self._initialized:
            return

        try:
            logger.info("Starting MCP manager initialization")
            await self.initialize_mcp_manager()
            logger.info("MCP manager initialization completed")
            self._initialized = True
        except Exception as e:
            logger.error(f"Error during MCP initialization: {e}")
            raise

    async def initialize_mcp_manager(self):
        """Initialize the MCPManager by creating connections for all server configurations."""
        tasks = []
        for config in self.server_configs:
            # Check for required environment variables before creating tasks
            server_id = config.id
            server_env_vars = config.env_vars

            logger.info(f"Checking environment variables for server '{server_id}'")
            missing_vars = []
            for var_name in server_env_vars:
                if not os.getenv(var_name):
                    missing_vars.append(var_name)
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

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Server {i + 1} initialization failed: {result}")
                else:
                    logger.info(f"Server {i + 1} initialization completed successfully")
        else:
            logger.warning(
                "No MCP servers to initialize - check configurations and environment variables"
            )

    async def create_mcp_connection(self, server_config: MCPServerConfig) -> MCPTools:
        """Initialize an MCP connection for a given server configuration.

        Args:
            server_config: MCPServerConfig object containing server configuration parameters

        Returns:
            MCPTools instance for the connected server

        Raises:
            Exception: If connection fails
        """
        server_id = server_config.id
        server_command = server_config.command
        server_args = server_config.args

        logger.info(f"Creating MCP connection for server '{server_id}'")
        # Create server parameters
        server_params = StdioServerParameters(
            command=server_command,
            args=server_args,
        )

        # Create the MCP connection
        try:
            logger.info(f"Attempting to connect to MCP server '{server_id}'")
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize MCP toolkit
                    mcp_tools = MCPTools(session=session)
                    await mcp_tools.initialize()
                    self.mcp_tools_map[server_id] = mcp_tools
                    logger.info(f"Successfully connected to MCP server '{server_id}'")
                    return mcp_tools
        except Exception as e:
            logger.error(
                f"Failed to create MCP connection for server '{server_id}': {e}"
            )
            raise

    def get_mcp_tools_list(self, server_id: Optional[str] = None) -> List[MCPTools]:
        """Get MCPTools instance(s) for a given server ID or all servers if no ID provided.

        Args:
            server_id: Optional ID of the server to get tools for. If None, returns tools for all servers.

        Returns:
            A list of MCPTools instances.

        Raises:
            KeyError: If the specified server_id doesn't exist.
        """
        if server_id is None:
            return list(self.mcp_tools_map.values())

        if server_id not in self.mcp_tools_map:
            available_servers = (
                ", ".join(self.mcp_tools_map.keys()) if self.mcp_tools_map else "none"
            )
            raise KeyError(
                f"No MCP connection found for server ID: {server_id}. Available servers: {available_servers}"
            )

        return [self.mcp_tools_map[server_id]]
