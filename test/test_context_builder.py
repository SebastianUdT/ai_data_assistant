from src.agent_context import AgentContext
from src.context_builder import build_context


def test_build_context():
    context = AgentContext(
        instructions="Be helpful."
    )

    context.add_message(
        "user",
        "Hello",
    )

    context.add_data(
        "customer",
        {
            "name": "Sebastian",
        },
    )

    result = build_context(context)

    assert "INSTRUCTIONS:" in result
    assert "Be helpful." in result

    assert "CONVERSATION:" in result
    assert "USER: Hello" in result

    assert "DATA:" in result
    assert "customer:" in result
    assert "Sebastian" in result


def test_context_message_limit():
    context = AgentContext()

    context.add_message(
        "user",
        "Message 1",
    )

    context.add_message(
        "assistant",
        "Message 2",
    )

    context.add_message(
        "user",
        "Message 3",
    )

    context.add_message(
        "assistant",
        "Message 4",
    )

    result = build_context(
        context,
        message_limit=2,
    )

    assert "Message 1" not in result
    assert "Message 2" not in result

    assert "Message 3" in result
    assert "Message 4" in result
def test_build_context_limits_messages():
    context = AgentContext()

    context.add_message(
        role="user",
        content="First message",
    )

    context.add_message(
        role="assistant",
        content="First response",
    )

    context.add_message(
        role="user",
        content="Second message",
    )

    context.add_message(
        role="assistant",
        content="Second response",
    )

    result = build_context(
        context,
        message_limit=2,
    )

    assert "First message" not in result
    assert "First response" not in result
    assert "Second message" in result
    assert "Second response" in result    
def test_context_can_update_summary():
    context = AgentContext()

    context.add_message(
        role="user",
        content="What is my balance?",
    )

    context.add_message(
        role="assistant",
        content="Your balance is $2500.",
    )

    context.update_summary()

    assert "user: What is my balance?" in context.summary
    assert "assistant: Your balance is $2500." in context.summary
def test_context_builder_includes_summary():
    context = AgentContext()

    context.add_message(
        role="user",
        content="What is my balance?",
    )

    context.add_message(
        role="assistant",
        content="Your balance is $2500.",
    )

    context.update_summary()

    result = build_context(context)

    assert "SUMMARY:" in result
    assert "user: What is my balance?" in result
    assert "assistant: Your balance is $2500." in result    

def test_context_builder_limits_recent_messages():
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

    result = build_context(
        context,
        message_limit=2,
    )

    assert "Message 1" not in result
    assert "Message 2" in result
    assert "Message 3" in result

def test_context_can_get_recent_context_messages():
    context = AgentContext()

    context.add_message(
        role="user",
        content="Old message",
    )

    context.add_message(
        role="assistant",
        content="Recent message",
    )

    messages = context.get_context_messages(
        recent_limit=1
    )

    assert len(messages) == 1
    assert messages[0].content == "Recent message"