from typing import Any

from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest
from src.tool_registry import ToolRegistry


def run_model_node(
    model: Model,
    request: ModelRequest,
) -> AgentResponse:
    return model.generate(
        request
    )


def run_tool_node(
    tool_registry: ToolRegistry,
    response: AgentResponse,
) -> Any:
    if not response.wants_tool:
        raise ValueError(
            "Tool node requires a tool request."
        )

    return tool_registry.execute(
        name=response.tool_name,
        arguments=response.arguments or {},
    )