from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest


class TestModel(Model):
    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        return AgentResponse(
            content="Test model response."
        )