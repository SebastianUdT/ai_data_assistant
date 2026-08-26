from src.local_mcp_server import LocalMCPServer
from src.mcp_client import MCPClient
from src.mcp_types import (
    MCPTool,
    MCPToolCall,
    MCPToolResult,
)


class LocalMCPClient(MCPClient):
    def __init__(
        self,
        server: LocalMCPServer,
    ):
        self.server = server

    def list_tools(
        self,
    ) -> list[MCPTool]:
        return self.server.list_tools()

    def call_tool(
        self,
        tool_call: MCPToolCall,
    ) -> MCPToolResult:
        return self.server.call_tool(
            tool_call
        )