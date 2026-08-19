from src.conversation import Message


class FakeModel:
    def generate(self, messages: list[Message]) -> str:
        last_message = messages[-1]["content"]

        if "name" in last_message.lower():
            return "Your name is Sebastian."

        return f"You said: {last_message}"