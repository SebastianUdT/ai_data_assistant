from src.agent_context import AgentContext


def build_context(
    context: AgentContext,
    message_limit: int | None = None,
) -> str:
    sections: list[str] = []

    if context.instructions:
        sections.append(
            f"INSTRUCTIONS:\n"
            f"{context.instructions}"
        )

    if context.summary:
        sections.append(
            f"SUMMARY:\n"
            f"{context.summary}"
        )

    messages = context.messages

    if message_limit is not None:
        messages = context.get_recent_messages(
            message_limit
        )

    if messages:
        message_lines = []

        for message in messages:
            line = (
                f"{message.role.upper()}: "
                f"{message.content}"
            )

            if message.metadata:
                if "result" in message.metadata:
                    line += (
                        f" {message.metadata['result']}"
                    )

                if "tool_name" in message.metadata:
                    line += (
                        f" tool={message.metadata['tool_name']}"
                    )

                if "arguments" in message.metadata:
                    line += (
                        f" arguments="
                        f"{message.metadata['arguments']}"
                    )

            message_lines.append(line)

        sections.append(
            "CONVERSATION:\n"
            + "\n".join(message_lines)
        )

    if context.data:
        data_lines = []

        for key, value in context.data.items():
            data_lines.append(
                f"{key}: {value}"
            )

        sections.append(
            "DATA:\n"
            + "\n".join(data_lines)
        )

    return "\n\n".join(sections)