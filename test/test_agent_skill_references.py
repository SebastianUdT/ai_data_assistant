from src.agent import Agent
from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest
from src.skill import Skill
from src.skill_registry import SkillRegistry
from src.tool_registry import ToolRegistry


class ReferenceInspectingModel(Model):
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
                "Analyze the financial data."
            ),
            references={
                "reporting_rules": (
                    "Never invent missing values."
                ),
                "output_format": (
                    "Include revenue, expenses, "
                    "and profit."
                ),
            },
        )
    )

    return registry


def test_agent_exposes_reference_names():
    model = ReferenceInspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
        skill_registry=create_skill_registry(),
    )

    agent.run(
        "Create a financial report."
    )

    assert model.request is not None

    skill_message = (
        model.request.messages[0]
    )

    assert (
        skill_message["metadata"][
            "available_references"
        ]
        == [
            "reporting_rules",
            "output_format",
        ]
    )


def test_agent_does_not_load_reference_contents():
    model = ReferenceInspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
        skill_registry=create_skill_registry(),
    )

    agent.run(
        "Create a financial report."
    )

    assert model.request is not None

    skill_message = (
        model.request.messages[0]
    )

    content = skill_message["content"]

    assert (
        "SKILL: financial_report"
        in content
    )

    assert (
        "Analyze the financial data."
        in content
    )

    assert (
        "Never invent missing values."
        not in content
    )

    assert (
        "Include revenue, expenses, and profit."
        not in content
    )

    assert (
        "REFERENCES:"
        not in content
    )