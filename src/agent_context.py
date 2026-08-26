from dataclasses import dataclass, field
from typing import Any

from src.conversation import Conversation, Message
from src.summarizer import summarize_messages


@dataclass
class AgentContext:
    instructions: str = ""
    summary: str = ""
    messages: list[Message] = field(
        default_factory=list
    )
    data: dict[str, Any] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    conversation: Conversation = field(
        default_factory=Conversation
    )

    def add_message(
        self,
        role: str,
        content: str,
    ) -> None:
        self.conversation.add_message(
            role=role,
            content=content,
        )

        self.messages = (
            self.conversation.get_messages()
        )

    def get_messages(
        self,
    ) -> list[Message]:
        return self.messages

    def get_recent_messages(
        self,
        limit: int,
    ) -> list[Message]:
        return self.messages[-limit:]

    def get_context_messages(
        self,
        limit: int | None = None,
        recent_limit: int | None = None,
        message_limit: int | None = None,
    ) -> list[Message]:
        selected_limit = (
            limit
            if limit is not None
            else recent_limit
            if recent_limit is not None
            else message_limit
        )

        if selected_limit is None:
            return self.messages

        return self.get_recent_messages(
            selected_limit
        )

    def update_summary(self) -> None:
        self.summary = summarize_messages(
            self.messages
        )

    def clear(self) -> None:
        self.conversation.clear()
        self.messages = []
        self.summary = ""

    def add_data(
        self,
        name: str,
        value: Any,
    ) -> None:
        self.data[name] = value

    def add_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> None:
        self.conversation.add_tool_call(
            tool_name=tool_name,
            arguments=arguments,
        )

        self.messages = (
            self.conversation.get_messages()
        )

    def add_tool_result(
        self,
        tool_name: str,
        result: dict[str, Any],
    ) -> None:
        self.conversation.add_tool_result(
            tool_name=tool_name,
            result=result,
        )

        self.messages = (
            self.conversation.get_messages()
        )