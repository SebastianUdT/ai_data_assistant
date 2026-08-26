from src.agent_context import AgentContext
from src.context_policy import ContextPolicy
from src.mcp_adapter import get_mcp_tool_schemas
from src.mcp_client import MCPClient
from src.memory_context import build_memory_context
from src.model_request import ModelRequest
from src.semantic_memory import MemoryEntry
from src.skill import Skill
from src.tool_registry import ToolRegistry


def build_model_request(
    context: AgentContext,
    tool_registry: ToolRegistry,
    message_limit: int | None = None,
    mcp_client: MCPClient | None = None,
    skill: Skill | None = None,
    memories: list[MemoryEntry] | None = None,
    context_policy: ContextPolicy | None = None,
) -> ModelRequest:
    policy = (
        context_policy
        if context_policy is not None
        else ContextPolicy()
    )

    recent_message_limit = (
        message_limit
        if message_limit is not None
        else policy.recent_message_limit
    )

    messages = context.get_context_messages(
        limit=recent_message_limit,
    )

    request_messages = [
        {
            "role": message.role,
            "content": message.content,
            "metadata": message.metadata,
        }
        for message in messages
    ]

    system_messages = []

    if skill is not None:
        system_messages.append(
            {
                "role": "system",
                "content": skill.build_context(
                    include_references=(
                        policy.include_skill_references
                    )
                ),
                "metadata": {
                    "skill": skill.name,
                    "available_references": (
                        skill.list_references()
                    ),
                },
            }
        )

    if memories:
        selected_memories = memories[
            :policy.max_memories
        ]

        memory_context = build_memory_context(
            selected_memories
        )

        if memory_context:
            system_messages.append(
                {
                    "role": "system",
                    "content": memory_context,
                    "metadata": {
                        "memory": True,
                    },
                }
            )

    request_messages = (
        system_messages
        + request_messages
    )

    tools = tool_registry.schemas()

    if mcp_client is not None:
        tools = (
            tools
            + get_mcp_tool_schemas(
                mcp_client
            )
        )

    return ModelRequest(
        messages=request_messages,
        tools=tools,
    )