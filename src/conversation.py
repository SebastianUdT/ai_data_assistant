from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    role: str
    content: str
    metadata: dict[str, Any] | None = None


class Conversation:
    def __init__(self):
        self.messages: list[Message] = []

    def add_message(
        self,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.messages.append(
            Message(
                role=role,
                content=content,
                metadata=metadata,
            )
        )

    def get_messages(self) -> list[Message]:
        return self.messages

    def clear(self) -> None:
        self.messages.clear()

    def add_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> None:
        self.add_message(
            role="tool_call",
            content="",
            metadata={
                "tool_name": tool_name,
                "arguments": arguments,
            },
        )

    def add_tool_result(
        self,
        tool_name: str,
        result: dict[str, Any],
    ) -> None:
        self.add_message(
            role="tool_result",
            content=str(result),
            metadata={
                "tool_name": tool_name,
                "result": result,
            },
        )