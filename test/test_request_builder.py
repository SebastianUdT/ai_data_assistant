from src.agent_context import AgentContext
from src.request_builder import build_model_request
from src.tool_registry import ToolRegistry


def test_request_builder_builds_messages():
    context = AgentContext()

    context.add_message(
        role="user",
        content="Hello",
    )

    registry = ToolRegistry()

    request = build_model_request(
        context=context,
        tool_registry=registry,
    )

    assert request.messages == [
        {
            "role": "user",
            "content": "Hello",
            "metadata": None,
        }
    ]

    assert request.tools == []


def test_request_builder_includes_tool_schemas():
    context = AgentContext()
    registry = ToolRegistry()

    def get_balance(
        customer_id: str,
    ) -> dict:
        return {
            "balance": 2500,
        }

    registry.register(
        name="get_balance",
        description="Get customer balance.",
        function=get_balance,
    )

    request = build_model_request(
        context=context,
        tool_registry=registry,
    )

    assert len(request.tools) == 1

    assert (
        request.tools[0]["name"]
        == "get_balance"
    )

    assert (
        request.tools[0]["description"]
        == "Get customer balance."
    )

    assert (
        "customer_id"
        in request.tools[0]["parameters"]
    )


def test_request_builder_limits_messages():
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

    registry = ToolRegistry()

    request = build_model_request(
        context=context,
        tool_registry=registry,
        message_limit=2,
    )

    assert len(request.messages) == 2

    assert (
        request.messages[0]["content"]
        == "Message 2"
    )

    assert (
        request.messages[1]["content"]
        == "Message 3"
    )