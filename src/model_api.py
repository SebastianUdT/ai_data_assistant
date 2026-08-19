from src.conversation import Message


def call_model_api(messages: list[Message]) -> dict:
    last_message = messages[-1]["content"]

    if "name" in last_message.lower():
        content = "Your name is Sebastian."
    else:
        content = f"You said: {last_message}"

    return {
        "id": "response-123",
        "model": "fake-model",
        "output": {
            "role": "assistant",
            "content": content,
        },
    }