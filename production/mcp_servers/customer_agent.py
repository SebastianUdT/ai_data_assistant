"""
Free Agent Workflow Simulation

Purpose:
    Simulate an agent selecting an MCP tool.

Architecture:
    Simulated Agent Decision
        -> MCP Client
        -> MCP Server
        -> CustomerService
        -> SQLite

No LLM, API key, or paid service required.
"""

import asyncio
import sys

from agents.mcp import MCPServerStdio


async def main() -> None:
    question = "What is the current balance of customer_001?"

    print(f"User question: {question}")

    # Simulate the tool selection an LLM would normally make.
    selected_tool = "get_customer_balance"
    arguments = {"customer_id": "customer_001"}

    print(f"Selected tool: {selected_tool}")
    print(f"Arguments: {arguments}")

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

        available_tools = await server.list_tools()
        tool_names = [tool.name for tool in available_tools]

        if selected_tool not in tool_names:
            raise RuntimeError(
                f"Required MCP tool not found: {selected_tool}"
            )

        result = await server.call_tool(
            selected_tool,
            arguments,
        )

        if result.isError:
            raise RuntimeError(
                f"MCP tool execution failed: {result.content}"
            )

        for item in result.content:
            if item.type == "text":
                print(f"Agent answer: {item.text}")


if __name__ == "__main__":
    asyncio.run(main())