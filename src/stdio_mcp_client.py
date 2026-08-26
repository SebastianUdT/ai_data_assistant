import asyncio
import json
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

from src.mcp_client import MCPClient
from src.mcp_types import (
    MCPTool,
    MCPToolCall,
    MCPToolResult,
)


class StdioMCPClient(MCPClient):
    def __init__(
        self,
        server_module: str = "src.real_mcp_server",
    ):
        self.server_module = server_module

    def list_tools(
        self,
    ) -> list[MCPTool]:
        return asyncio.run(
            self._list_tools()
        )

    def call_tool(
        self,
        tool_call: MCPToolCall,
    ) -> MCPToolResult:
        return asyncio.run(
            self._call_tool(
                tool_call
            )
        )

    def _server_parameters(
        self,
    ) -> StdioServerParameters:
        return StdioServerParameters(
            command=sys.executable,
            args=[
                "-m",
                self.server_module,
            ],
        )

    async def _list_tools(
        self,
    ) -> list[MCPTool]:
        server_params = (
            self._server_parameters()
        )

        async with stdio_client(
            server_params
        ) as (read, write):

            async with ClientSession(
                read,
                write,
            ) as session:

                await session.initialize()

                response = (
                    await session.list_tools()
                )

                return [
                    MCPTool(
                        name=tool.name,
                        description=(
                            tool.description or ""
                        ),
                        parameters=(
                            self._convert_schema(
                                tool.input_schema
                            )
                        ),
                    )
                    for tool in response.tools
                ]

    async def _call_tool(
        self,
        tool_call: MCPToolCall,
    ) -> MCPToolResult:
        server_params = (
            self._server_parameters()
        )

        async with stdio_client(
            server_params
        ) as (read, write):

            async with ClientSession(
                read,
                write,
            ) as session:

                await session.initialize()

                response = await session.call_tool(
                    tool_call.name,
                    arguments=tool_call.arguments,
                )

                if response.is_error:
                    error_text = (
                        self._extract_text(
                            response.content
                        )
                    )

                    return MCPToolResult(
                        name=tool_call.name,
                        result={
                            "error": error_text,
                            "tool": tool_call.name,
                        },
                        is_error=True,
                    )

                result = self._extract_result(
                    response
                )

                return MCPToolResult(
                    name=tool_call.name,
                    result=result,
                    is_error=False,
                )

    @staticmethod
    def _convert_schema(
        input_schema: dict[str, Any],
    ) -> dict[str, Any]:
        properties = input_schema.get(
            "properties",
            {},
        )

        required = set(
            input_schema.get(
                "required",
                [],
            )
        )

        parameters: dict[str, Any] = {}

        for name, schema in properties.items():
            parameters[name] = {
                "type": schema.get(
                    "type",
                    "unknown",
                ),
                "required": name in required,
            }

        return parameters

    @staticmethod
    def _extract_text(
        content: list[Any],
    ) -> str:
        parts = [
            block.text
            for block in content
            if isinstance(
                block,
                TextContent,
            )
        ]

        return "\n".join(parts)

    def _extract_result(
        self,
        response: Any,
    ) -> Any:
        if (
            response.structured_content
            is not None
        ):
            return response.structured_content

        text = self._extract_text(
            response.content
        )

        if not text:
            return None

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text