from enum import Enum

from src.agent_model import AgentResponse


class AgentNode(str, Enum):
    MODEL = "model"
    TOOL = "tool"
    END = "end"


def get_next_node(
    response: AgentResponse,
) -> AgentNode:
    if response.wants_tool:
        return AgentNode.TOOL

    return AgentNode.END