from src.conversation import Message


def summarize_messages(
    messages: list[Message],
) -> str:
    if not messages:
        return ""

    parts: list[str] = []

    for message in messages:
        parts.append(
            f"{message.role}: {message.content}"
        )

    return " | ".join(parts)
