from abc import ABC, abstractmethod

from src.mcp_types import (
    MCPTool,
    MCPToolCall,
    MCPToolResult,
)


class MCPClient(ABC):

    @abstractmethod
    def list_tools(
        self,
    ) -> list[MCPTool]:
        pass

    @abstractmethod
    def call_tool(
        self,
        tool_call: MCPToolCall,
    ) -> MCPToolResult:
        pass