"""
Verify that the production application can connect to our MCP server.

This tests real MCP communication without requiring an LLM call.
"""

import asyncio
import sys

from agents.mcp import MCPServerStdio


async def main() -> None:

    async with MCPServerStdio(
        name="Customer Finance",
        params={
            "command": sys.executable,
            "args": [
                "-m",
                "production.mcp_servers.customer_server",
            ],
        },
    ) as server:

        # Discover the tools published by the MCP server.
        tools = await server.list_tools()

        print(
            "Available MCP tools:",
            [tool.name for tool in tools],
        )

        # Call the MCP tool through the real protocol.
        result = await server.call_tool(
            "get_customer_balance",
            {
                "customer_id": "customer_001",
            },
        )

        print("MCP result:", result)


if __name__ == "__main__":
    asyncio.run(main())