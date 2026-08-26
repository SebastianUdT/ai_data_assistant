from src.conversation import Message
from src.summarizer import summarize_messages


def test_summarize_messages():
    messages = [
        Message(
            role="user",
            content="My name is Sebastian.",
        ),
        Message(
            role="assistant",
            content="Nice to meet you.",
        ),
    ]

    result = summarize_messages(messages)

    assert "My name is Sebastian." in result
    assert "Nice to meet you." in result


def test_summarize_empty_messages():
    result = summarize_messages([])

    assert result == ""