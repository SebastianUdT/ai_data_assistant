from typing import Any

from src.mcp_client import MCPClient


def get_mcp_tool_schemas(
    client: MCPClient,
) -> list[dict[str, Any]]:
    tools = client.list_tools()

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        }
        for tool in tools
    ]