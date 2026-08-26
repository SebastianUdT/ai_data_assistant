from src.agent import Agent
from src.agent_model import AgentResponse
from src.harness import (
    AgentHarness,
    HarnessConfig,
)
from src.model import Model
from src.model_request import ModelRequest
from src.result_validator import ExpectedTextValidator
from src.tool_registry import ToolRegistry


class CorrectingModel(Model):
    def __init__(
        self,
    ) -> None:
        self.calls = 0

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        self.calls += 1

        latest_message = (
            request.messages[-1]["content"]
        )

        if (
            "VALIDATION FEEDBACK:"
            in latest_message
        ):
            return AgentResponse(
                content=(
                    "The correct answer is 2500."
                )
            )

        return AgentResponse(
            content="The answer is wrong."
        )


class AlwaysWrongModel(Model):
    def __init__(
        self,
    ) -> None:
        self.calls = 0

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        self.calls += 1

        return AgentResponse(
            content="Still wrong."
        )


def test_harness_returns_result_without_validator():
    model = CorrectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    harness = AgentHarness()

    result = harness.run(
        agent=agent,
        task="Find the correct answer.",
    )

    assert result == "The answer is wrong."

    assert model.calls == 1


def test_harness_accepts_valid_result():
    model = CorrectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    harness = AgentHarness()

    validator = ExpectedTextValidator(
        expected_text="wrong"
    )

    result = harness.run(
        agent=agent,
        task="Find the correct answer.",
        validator=validator,
    )

    assert result == "The answer is wrong."

    assert model.calls == 1


def test_harness_retries_after_validation_failure():
    model = CorrectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    harness = AgentHarness()

    validator = ExpectedTextValidator(
        expected_text="2500"
    )

    result = harness.run(
        agent=agent,
        task="Find the correct answer.",
        validator=validator,
    )

    assert (
        result
        == "The correct answer is 2500."
    )

    assert model.calls == 2


def test_harness_passes_feedback_to_agent():
    model = CorrectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    harness = AgentHarness()

    validator = ExpectedTextValidator(
        expected_text="2500"
    )

    harness.run(
        agent=agent,
        task="Find the correct answer.",
        validator=validator,
    )

    messages = (
        agent.conversation.get_messages()
    )

    feedback_messages = [
        message
        for message in messages
        if (
            message.role == "user"
            and "VALIDATION FEEDBACK:"
            in message.content
        )
    ]

    assert len(feedback_messages) == 1

    assert (
        "Expected result to contain: 2500"
        in feedback_messages[0].content
    )

    assert (
        "Try again and correct the problem."
        in feedback_messages[0].content
    )


def test_harness_stops_after_max_validation_attempts():
    model = AlwaysWrongModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    harness = AgentHarness(
        config=HarnessConfig(
            max_validation_attempts=2,
        )
    )

    validator = ExpectedTextValidator(
        expected_text="2500"
    )

    try:
        harness.run(
            agent=agent,
            task="Find the correct answer.",
            validator=validator,
        )

        assert False

    except RuntimeError as error:
        assert (
            str(error)
            == (
                "Harness validation failed after "
                "2 attempts."
            )
        )

    assert model.calls == 2