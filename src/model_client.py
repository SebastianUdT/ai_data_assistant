from src.conversation import Message
from src.model_api import call_model_api


class ModelClient:
    def generate(self, messages: list[Message]) -> str:
        response = call_model_api(messages)

        return response["output"]["content"]