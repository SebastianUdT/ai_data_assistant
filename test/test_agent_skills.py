from src.agent import Agent
from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest
from src.skill import Skill
from src.skill_registry import SkillRegistry
from src.tool_registry import ToolRegistry


class SkillInspectingModel(Model):
    def __init__(
        self,
    ) -> None:
        self.request: ModelRequest | None = None

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        self.request = request

        return AgentResponse(
            content="Done."
        )


def create_skill_registry() -> SkillRegistry:
    registry = SkillRegistry()

    registry.register(
        Skill(
            name="financial_report",
            description=(
                "Create monthly financial reports."
            ),
            instructions=(
                "Retrieve revenue and expenses. "
                "Calculate profit. "
                "Never invent missing values."
            ),
        )
    )

    registry.register(
        Skill(
            name="customer_support",
            description=(
                "Handle customer support requests."
            ),
            instructions=(
                "Understand the customer's problem "
                "and provide a clear response."
            ),
        )
    )

    return registry


def test_agent_loads_matching_skill():
    model = SkillInspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
        skill_registry=create_skill_registry(),
    )

    result = agent.run(
        "Create a financial report for this month."
    )

    assert result == "Done."

    assert model.request is not None

    messages = model.request.messages

    assert len(messages) == 2

    assert messages[0]["role"] == "system"

    assert (
        messages[0]["metadata"]["skill"]
        == "financial_report"
    )

    assert (
        "SKILL: financial_report"
        in messages[0]["content"]
    )

    assert (
        "Never invent missing values."
        in messages[0]["content"]
    )

    assert messages[1] == {
        "role": "user",
        "content": (
            "Create a financial report "
            "for this month."
        ),
        "metadata": None,
    }


def test_agent_does_not_load_unrelated_skill():
    model = SkillInspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
        skill_registry=create_skill_registry(),
    )

    result = agent.run(
        "Hello"
    )

    assert result == "Done."

    assert model.request is not None

    messages = model.request.messages

    assert len(messages) == 1

    assert messages[0] == {
        "role": "user",
        "content": "Hello",
        "metadata": None,
    }