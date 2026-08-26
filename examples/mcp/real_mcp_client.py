import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "src.real_mcp_server",
        ],
    )

    async with stdio_client(
        server_params
    ) as (read, write):

        async with ClientSession(
            read,
            write,
        ) as session:

            await session.initialize()

            tools_response = await session.list_tools()

            print("Available tools:")

            for tool in tools_response.tools:
                print(
                    f"- {tool.name}: "
                    f"{tool.description}"
                )

            result = await session.call_tool(
                "get_customer_balance",
                arguments={
                    "customer_id": "customer_001",
                },
            )

            print()
            print("Tool result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(
        main()
    )