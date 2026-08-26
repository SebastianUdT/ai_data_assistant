from typing import Protocol

from src.conversation import Message


class Model(Protocol):
    def generate(self, messages: list[Message]) -> str:
        ...