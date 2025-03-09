from mcp_manager import MCPManager, mcp_server_configs


def main():
    # MCP server configurations to test
    server_configs = list(mcp_server_configs.keys())
    # Initialize the MCP manager
    mcp_manager = MCPManager.create_sync(server_configs)
    mcp_tools = mcp_manager.get_mcp_tools_list()

    # Print the MCPTools objects
    for idx, mcp_tool in enumerate(mcp_tools, start=1):
        print(f"MCPTools {idx}: {mcp_tool}")


if __name__ == "__main__":
    main()
