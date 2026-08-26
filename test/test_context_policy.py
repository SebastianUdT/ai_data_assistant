from src.agent_context import AgentContext
from src.context_policy import ContextPolicy
from src.request_builder import build_model_request
from src.semantic_memory import MemoryEntry
from src.tool_registry import ToolRegistry


def test_context_policy_limits_messages_and_memories():
    context = AgentContext()

    context.add_message(
        role="user",
        content="Message 1",
    )

    context.add_message(
        role="assistant",
        content="Message 2",
    )

    context.add_message(
        role="user",
        content="Message 3",
    )

    memories = [
        MemoryEntry(
            key="memory_1",
            value="Value 1",
        ),
        MemoryEntry(
            key="memory_2",
            value="Value 2",
        ),
        MemoryEntry(
            key="memory_3",
            value="Value 3",
        ),
    ]

    policy = ContextPolicy(
        recent_message_limit=2,
        max_memories=2,
    )

    request = build_model_request(
        context=context,
        tool_registry=ToolRegistry(),
        memories=memories,
        context_policy=policy,
    )

    memory_messages = [
        message
        for message in request.messages
        if (
            message["metadata"] is not None
            and message["metadata"].get(
                "memory"
            )
        )
    ]

    assert len(memory_messages) == 1

    memory_content = (
        memory_messages[0]["content"]
    )

    assert "memory_1: Value 1" in memory_content
    assert "memory_2: Value 2" in memory_content
    assert "memory_3: Value 3" not in memory_content

    conversation_messages = [
        message
        for message in request.messages
        if not (
            message["metadata"] is not None
            and message["metadata"].get(
                "memory"
            )
        )
    ]

    assert len(conversation_messages) == 2

    assert (
        conversation_messages[0]["content"]
        == "Message 2"
    )

    assert (
        conversation_messages[1]["content"]
        == "Message 3"
    )