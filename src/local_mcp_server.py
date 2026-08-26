from src.mcp_types import (
    MCPTool,
    MCPToolCall,
    MCPToolResult,
)
from src.tool_registry import ToolRegistry


class LocalMCPServer:
    def __init__(
        self,
        tool_registry: ToolRegistry,
    ):
        self.tool_registry = tool_registry

    def list_tools(
        self,
    ) -> list[MCPTool]:
        tools: list[MCPTool] = []

        for schema in self.tool_registry.schemas():
            tools.append(
                MCPTool(
                    name=schema["name"],
                    description=schema["description"],
                    parameters=schema["parameters"],
                )
            )

        return tools

    def call_tool(
        self,
        tool_call: MCPToolCall,
    ) -> MCPToolResult:
        result = self.tool_registry.execute(
            name=tool_call.name,
            arguments=tool_call.arguments,
        )

        is_error = (
            isinstance(result, dict)
            and "error" in result
        )

        return MCPToolResult(
            name=tool_call.name,
            result=result,
            is_error=is_error,
        )