"""
Production Agent Evaluation

Evaluates tool selection using the real Agents SDK
with ScriptedModel.

No OpenAI API calls or paid services.
"""

import asyncio

from agents import Runner

from production.agent import (
    ScriptedModel,
    assistant_message,
    finance_agent,
    function_call,
)


def evaluate_tool_selection(
    selected_tool: str,
    expected_tool: str,
) -> dict:
    """
    Run a deterministic agent scenario.

    PASS requires the expected tool to appear in
    the actual execution trace.
    """

    model = ScriptedModel(
        [
            [
                function_call(
                    selected_tool,
                    {"customer_id": "customer_001"},
                    call_id="evaluation_call_001",
                )
            ],
            [
                assistant_message("Evaluation completed.")
            ],
        ]
    )

    # Use a test-specific agent instance to avoid modifying
    # the shared production agent.
    from dataclasses import replace

    agent = replace(finance_agent, model=model)

    result = asyncio.run(
        Runner.run(
            agent,
            "What is the balance of customer_001?",
            max_turns=5,
        )
    )

    called_tools = []

    for item in result.new_items:
        raw_item = getattr(item, "raw_item", None)

        if getattr(raw_item, "type", None) == "function_call":
            called_tools.append(raw_item.name)

    return {
        "expected_tool": expected_tool,
        "called_tools": called_tools,
        "passed": expected_tool in called_tools,
    }


def test_correct_tool_selection():
    evaluation = evaluate_tool_selection(
        selected_tool="get_customer_balance",
        expected_tool="get_customer_balance",
    )

    assert evaluation["passed"] is True


def test_wrong_tool_selection_is_detected():
    evaluation = evaluate_tool_selection(
        selected_tool="get_customer_balance",
        expected_tool="apply_customer_credit",
    )

    assert evaluation["passed"] is False