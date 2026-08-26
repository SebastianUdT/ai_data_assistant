from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPTool:
    name: str
    description: str
    parameters: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MCPToolCall:
    name: str
    arguments: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class MCPToolResult:
    name: str
    result: Any
    is_error: bool = False