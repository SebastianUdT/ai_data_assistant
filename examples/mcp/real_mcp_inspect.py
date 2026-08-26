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

            resources = await session.list_resources()

            print("Resources:")

            for resource in resources.resources:
                print(
                    f"- {resource.uri}: "
                    f"{resource.name}"
                )

            resource_result = await session.read_resource(
                "customer://customer_001"
            )

            print()
            print("Resource result:")
            print(resource_result)

            prompts = await session.list_prompts()

            print()
            print("Prompts:")

            for prompt in prompts.prompts:
                print(
                    f"- {prompt.name}: "
                    f"{prompt.description}"
                )

            prompt_result = await session.get_prompt(
                "explain_balance",
                arguments={
                    "customer_name": "Sebastian",
                    "balance": "2500",
                },
            )

            print()
            print("Prompt result:")
            print(prompt_result)


if __name__ == "__main__":
    asyncio.run(
        main()
    )