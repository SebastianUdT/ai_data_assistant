from src.agent import Agent
from src.subagent import Subagent
from src.subagent_delegator import SubagentDelegator
from src.subagent_registry import SubagentRegistry
from src.subagent_selector import SubagentSelector
from src.test_model import TestModel
from src.tool_registry import ToolRegistry


def create_subagent(
    name: str,
    description: str,
) -> Subagent:
    agent = Agent(
        tool_registry=ToolRegistry(),
        model=TestModel(),
    )

    return Subagent(
        name=name,
        description=description,
        agent=agent,
    )


def create_delegator() -> tuple[
    SubagentDelegator,
    SubagentRegistry,
]:
    registry = SubagentRegistry()

    registry.register(
        create_subagent(
            name="finance",
            description=(
                "Handle financial analysis "
                "and reporting."
            ),
        )
    )

    registry.register(
        create_subagent(
            name="support",
            description=(
                "Handle customer support requests."
            ),
        )
    )

    selector = SubagentSelector(
        registry=registry,
    )

    delegator = SubagentDelegator(
        selector=selector,
    )

    return delegator, registry


def test_delegator_runs_selected_subagent():
    delegator, _ = create_delegator()

    result = delegator.delegate(
        "Create a financial report."
    )

    assert result.subagent_name == "finance"

    assert (
        result.task
        == "Create a financial report."
    )

    assert (
        result.result
        == "Test model response."
    )


def test_delegator_can_use_different_subagent():
    delegator, _ = create_delegator()

    result = delegator.delegate(
        "I need customer support."
    )

    assert result.subagent_name == "support"

    assert (
        result.result
        == "Test model response."
    )


def test_delegator_rejects_unknown_task():
    delegator, _ = create_delegator()

    try:
        delegator.delegate(
            "Hello"
        )

        assert False

    except ValueError as error:
        assert (
            str(error)
            == "No suitable subagent found."
        )


def test_subagent_context_is_isolated():
    delegator, registry = create_delegator()

    finance = registry.get(
        "finance"
    )

    support = registry.get(
        "support"
    )

    delegator.delegate(
        "Create a financial report."
    )

    finance_messages = (
        finance.agent.conversation.get_messages()
    )

    support_messages = (
        support.agent.conversation.get_messages()
    )

    assert len(finance_messages) == 2

    assert (
        finance_messages[0].role
        == "user"
    )

    assert (
        finance_messages[0].content
        == "Create a financial report."
    )

    assert (
        finance_messages[1].role
        == "assistant"
    )

    assert support_messages == []


def test_parent_and_subagent_contexts_are_separate():
    delegator, registry = create_delegator()

    parent = Agent(
        tool_registry=ToolRegistry(),
        model=TestModel(),
    )

    parent.run(
        "This belongs to the parent."
    )

    delegator.delegate(
        "Create a financial report."
    )

    finance = registry.get(
        "finance"
    )

    parent_messages = (
        parent.conversation.get_messages()
    )

    finance_messages = (
        finance.agent.conversation.get_messages()
    )

    assert (
        parent_messages[0].content
        == "This belongs to the parent."
    )

    assert (
        finance_messages[0].content
        == "Create a financial report."
    )

    assert all(
        message.content
        != "This belongs to the parent."
        for message in finance_messages
    )

    assert all(
        message.content
        != "Create a financial report."
        for message in parent_messages
    )
    