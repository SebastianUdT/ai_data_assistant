
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentResponse:
    content: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None

    @property
    def wants_tool(self) -> bool:
        return self.tool_name is not None


