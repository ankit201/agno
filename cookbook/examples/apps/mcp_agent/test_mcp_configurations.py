import asyncio

from mcp_manager import MCPManager, MCPServerConfig


async def async_main():
    # MCP server configurations to test
    server_configs = [
        MCPServerConfig(
            id="github",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env_vars=["GITHUB_TOKEN"],
        ),
        MCPServerConfig(
            id="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", "."],
        ),
        MCPServerConfig(
            id="memory",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
        ),
        MCPServerConfig(
            id="git",
            command="uvx",
            args=["mcp-server-git"],
        ),
        MCPServerConfig(
            id="brave-search",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-brave-search"],
            env_vars=["BRAVE_API_KEY"],
        ),
    ]

    # Initialize the MCP manager
    mcp_manager = await MCPManager.create(server_configs)
    mcp_tools = mcp_manager.get_mcp_tools_list()

    # Print the MCPTools objects
    for idx, mcp_tool in enumerate(mcp_tools, start=1):
        print(f"MCPTools {idx}: {mcp_tool}")


if __name__ == "__main__":
    asyncio.run(async_main())
