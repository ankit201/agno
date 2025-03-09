import asyncio

from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPManager:
    """
    Wrapper class to hold the persistent MCPTools along with the underlying client manager
    and session. Keeping a reference to the client manager prevents the session from
    being closed.
    """

    def __init__(self, mcp_tools: MCPTools, client_manager, session: ClientSession):
        self.mcp_tools = mcp_tools
        self.client_manager = client_manager
        self.session = session


async def create_persistent_mcp(server_param: StdioServerParameters) -> PersistentMCP:
    """
    Create a persistent MCPTools instance for a given server parameter.
    Manually enters the client manager so that the session remains open.
    """
    # Create the client manager and manually enter its context to get the connection
    client_manager = stdio_client(server_param)
    read, write = await client_manager.__aenter__()
    session = ClientSession(read, write)

    # Initialize MCPTools with the persistent session
    mcp_tools = MCPTools(session=session)
    await mcp_tools.initialize()

    return PersistentMCP(mcp_tools, client_manager, session)


async def initialize_all(server_params_list):
    """
    Given a list of server parameters, concurrently initialize all persistent MCPTools.
    """
    tasks = [create_persistent_mcp(param) for param in server_params_list]
    return await asyncio.gather(*tasks)


def get_persistent_mcp_tools_list(server_params_list):
    """
    Initialize multiple MCPTools objects without using 'async with', so that the sessions remain open.

    Parameters:
      server_params_list: List of StdioServerParameters objects.

    Returns:
      A list of PersistentMCP objects. Each object contains:
        - mcp_tools: The initialized MCPTools instance.
        - client_manager: The underlying client manager (kept alive to avoid session closure).
        - session: The active ClientSession.
    """
    return asyncio.run(initialize_all(server_params_list))


# Example usage:
if __name__ == "__main__":
    # Define server parameters for different servers.
    server_params1 = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    )
    server_params2 = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-other"],
    )
    server_params_list = [server_params1, server_params2]

    # Get the persistent MCP connections.
    persistent_mcps = get_persistent_mcp_tools_list(server_params_list)

    # Extract the MCPTools instances (for example, to add to your agent).
    mcp_tools_list = [persistent_mcp.mcp_tools for persistent_mcp in persistent_mcps]

    # Print the MCPTools objects for demonstration.
    for idx, mcp_tool in enumerate(mcp_tools_list, start=1):
        print(f"Persistent MCPTools {idx}: {mcp_tool}")
