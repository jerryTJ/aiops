
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool


class LiquibaseTool(BaseTool):
    name = "liquibase"
    description = "用于执行 Liquibase 相关操作的工具" 


async def list_tools() -> list[BaseTool]:
    """
    列出 MCP 客户端中的所有工具
    """ 
    client = MultiServerMCPClient({
            "database": {
                "transport": "streamable_http",
                # Replace with your actual server URL and port
                "url": "http://127.0.0.1:3000/mcp",
            }
    })

    # Load tools from your MCP server
    tools = await client.get_tools()
    # Print available tools
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"  Description: {tool.description}")
        print("Tool:", tool.name, " strict=", getattr(tool, "strict", None))
    return tools
