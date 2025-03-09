import asyncio

from mcp_manager import MCPManager


def main():
    test_server_configs = [
        {
            "id": "github",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env_vars": {"GITHUB_TOKEN": "GitHub Personal Access Token"},
        },
    ]

    mcp_manager = MCPManager(test_server_configs)
    mcp_tools = mcp_manager.get_mcp_tools()

    # Print the MCPTools objects for demonstration.
    for idx, mcp_tool in enumerate(mcp_tools, start=1):
        print(f"MCPTools {idx}: {mcp_tool}")

    # Clean up connections before exiting - now using non-async version
    mcp_manager.cleanup()


if __name__ == "__main__":
    main()
