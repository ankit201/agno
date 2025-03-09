import asyncio

from mcp_manager import MCPManager


def main():
    server_configs = [
        {
            "id": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env_vars": {"GITHUB_TOKEN": "GitHub Personal Access Token"},
        },
        {
            "id": "filesystem",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
        },
        {
            "id": "memory",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
        {
            "id": "git",
            "command": "uvx",
            "args": ["mcp-server-git"],
        },
        {
            "id": "brave-search",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env_vars": {"BRAVE_API_KEY": "Your Brave API Key"},
        },
    ]

    mcp_manager = MCPManager(server_configs)
    mcp_tools = mcp_manager.get_mcp_tools()

    # Print the MCPTools objects for demonstration.
    for idx, mcp_tool in enumerate(mcp_tools, start=1):
        print(f"MCPTools {idx}: {mcp_tool}")

    # Clean up connections before exiting - now using non-async version
    mcp_manager.cleanup()


if __name__ == "__main__":
    main()
