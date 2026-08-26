from src.agent import create_agent
from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest
from src.semantic_memory import SemanticMemory


class MemoryInspectingModel(Model):
    def __init__(self):
        self.last_request: ModelRequest | None = None

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        self.last_request = request

        return AgentResponse(
            content="The report currency is CLP."
        )


def test_agent_retrieves_semantic_memory():
    memory = SemanticMemory()

    memory.add(
        key="report_currency",
        value="CLP",
        metadata={
            "customer_id": "customer_001",
        },
    )

    model = MemoryInspectingModel()

    agent = create_agent(
        model=model,
        semantic_memory=memory,
    )

    result = agent.run(
        "What currency should the report use?"
    )

    assert result == (
        "The report currency is CLP."
    )

    assert model.last_request is not None

    memory_messages = [
        message
        for message in model.last_request.messages
        if (
            message["metadata"] is not None
            and message["metadata"].get(
                "memory"
            )
        )
    ]

    assert len(memory_messages) == 1

    assert (
        "report_currency: CLP"
        in memory_messages[0]["content"]
    )