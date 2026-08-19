from src.conversation import (
    Message,
    add_message,
    create_conversation,
)
from src.model import Model
from src.model_client import ModelClient


def run_chat(model: Model) -> None:
    conversation: list[Message] = create_conversation()

    print("AI Data Assistant")
    print("Type 'exit' to quit.")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            break

        add_message(
            conversation,
            "user",
            user_input,
        )

        response = model.generate(conversation)

        add_message(
            conversation,
            "assistant",
            response,
        )

        print(f"Assistant: {response}")


def main() -> None:
    model = ModelClient()
    run_chat(model)


if __name__ == "__main__":
    main()