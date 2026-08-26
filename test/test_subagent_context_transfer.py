from src.agent import Agent
from src.delegation_context import DelegationContext
from src.subagent import Subagent
from src.subagent_delegator import SubagentDelegator
from src.subagent_registry import SubagentRegistry
from src.subagent_selector import SubagentSelector
from src.test_model import TestModel
from src.tool_registry import ToolRegistry


def create_delegator() -> tuple[
    SubagentDelegator,
    SubagentRegistry,
]:
    registry = SubagentRegistry()

    finance_agent = Agent(
        tool_registry=ToolRegistry(),
        model=TestModel(),
    )

    registry.register(
        Subagent(
            name="finance",
            description=(
                "Handle financial analysis "
                "and reporting."
            ),
            agent=finance_agent,
        )
    )

    selector = SubagentSelector(
        registry=registry,
    )

    delegator = SubagentDelegator(
        selector=selector,
    )

    return delegator, registry


def test_delegator_transfers_selected_context():
    delegator, registry = create_delegator()

    context = DelegationContext(
        data={
            "customer_id": "customer_001",
            "period": "August 2026",
        },
        instructions=(
            "Do not invent missing values."
        ),
    )

    delegator.delegate(
        "Create a financial report.",
        context=context,
    )

    finance = registry.get(
        "finance"
    )

    messages = (
        finance.agent.conversation.get_messages()
    )

    delegated_message = messages[0].content

    assert (
        "TASK:\n"
        "Create a financial report."
        in delegated_message
    )

    assert (
        "INSTRUCTIONS:\n"
        "Do not invent missing values."
        in delegated_message
    )

    assert (
        "customer_id: customer_001"
        in delegated_message
    )

    assert (
        "period: August 2026"
        in delegated_message
    )


def test_parent_context_does_not_transfer_automatically():
    delegator, registry = create_delegator()

    parent = Agent(
        tool_registry=ToolRegistry(),
        model=TestModel(),
    )

    parent.context.add_data(
        "secret_parent_data",
        "do-not-transfer",
    )

    parent.run(
        "This conversation belongs "
        "to the parent."
    )

    context = DelegationContext(
        data={
            "customer_id": "customer_001",
        }
    )

    delegator.delegate(
        "Create a financial report.",
        context=context,
    )

    finance = registry.get(
        "finance"
    )

    messages = (
        finance.agent.conversation.get_messages()
    )

    delegated_message = messages[0].content

    assert (
        "customer_id: customer_001"
        in delegated_message
    )

    assert (
        "secret_parent_data"
        not in delegated_message
    )

    assert (
        "do-not-transfer"
        not in delegated_message
    )

    assert (
        "This conversation belongs "
        "to the parent."
        not in delegated_message
    )


def test_delegation_without_context_stays_simple():
    delegator, registry = create_delegator()

    delegator.delegate(
        "Create a financial report."
    )

    finance = registry.get(
        "finance"
    )

    messages = (
        finance.agent.conversation.get_messages()
    )

    assert (
        messages[0].content
        == "Create a financial report."
    )