from typing import Literal, TypedDict


Role = Literal["system", "user", "assistant"]


class Message(TypedDict):
    role: Role
    content: str


def create_conversation() -> list[Message]:
    return [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
        }
    ]


def add_message(
    conversation: list[Message],
    role: Role,
    content: str,
) -> None:
    conversation.append(
        {
            "role": role,
            "content": content,
        }
    )