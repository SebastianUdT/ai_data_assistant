"""
Production Subagent Tests

Verify:
1. The analysis subagent has no financial tools.
2. The Finance Agent exposes the analysis subagent.
3. Financial approval requirements remain intact.
4. Runtime delegation executes through the Agents SDK.

All tests use ScriptedModel.
No paid API calls.
"""

import asyncio

from agents import Runner

from production.agent import (
    ScriptedModel,
    assistant_message,
    function_call,
)
from production.analysis_subagent import (
    create_analysis_subagent,
    create_finance_agent_with_subagent,
)


def test_analysis_subagent_is_read_only():
    specialist = create_analysis_subagent()

    assert specialist.name == "Customer Analysis Specialist"
    assert specialist.tools == []


def test_finance_agent_exposes_analysis_subagent():
    agent = create_finance_agent_with_subagent()

    tool_names = [tool.name for tool in agent.tools]

    assert "analyze_customer_information" in tool_names
    assert "get_customer_balance" in tool_names
    assert "apply_customer_credit" in tool_names


def test_financial_approval_is_preserved():
    agent = create_finance_agent_with_subagent()

    credit_tool = next(
        tool
        for tool in agent.tools
        if tool.name == "apply_customer_credit"
    )

    assert credit_tool.needs_approval is True


def test_runtime_subagent_delegation():
    """
    Finance Agent -> Analysis Subagent -> Finance Agent.

    The parent and specialist have separate scripted models.
    """

    specialist_model = ScriptedModel(
        [
            [
                assistant_message(
                    "The customer has a stable financial profile."
                )
            ]
        ]
    )

    finance_model = ScriptedModel(
        [
            [
                function_call(
                    "analyze_customer_information",
                    {
                        "input": (
                            "Analyze the customer's financial profile."
                        )
                    },
                    call_id="analysis_call_001",
                )
            ],
            [
                assistant_message(
                    "Analysis complete: "
                    "the customer has a stable financial profile."
                )
            ],
        ]
    )

    agent = create_finance_agent_with_subagent(
        analysis_model=specialist_model,
    )

    # The factory reuses the existing Finance Agent's model.
    # Replace only the model on this test-specific instance.
    agent.model = finance_model

    result = asyncio.run(
        Runner.run(
            agent,
            "Analyze this customer's financial profile.",
            max_turns=5,
        )
    )

    assert "stable financial profile" in result.final_output

    # Confirm that the parent actually called the subagent.
    assert any(
        getattr(item, "name", None)
        == "analyze_customer_information"
        for item in result.new_items
    ) or any(
        getattr(getattr(item, "raw_item", None), "name", None)
        == "analyze_customer_information"
        for item in result.new_items
    )