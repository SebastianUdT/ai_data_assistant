"""
Production Analysis Subagent

Purpose:
    Provide a read-only specialist that the Finance Agent
    can call for customer-related analysis.

Security:
    The subagent has no financial modification tools.
    The existing Finance Agent retains its own authorization
    and human approval requirements.

No paid API is required when using ScriptedModel.
"""

from agents import Agent

from production.agent import ScriptedModel, finance_agent


def create_analysis_subagent(
    model: ScriptedModel | None = None,
) -> Agent:
    """
    Create an isolated, read-only analysis agent.

    We deliberately do not attach the financial tools
    available to the main Finance Agent.
    """

    return Agent(
        name="Customer Analysis Specialist",
        instructions=(
            "You are a customer analysis specialist. "
            "Analyze only the information supplied to you. "
            "Return concise, factual summaries. "
            "Do not invent customer information. "
            "You cannot change balances, approve transactions, "
            "or perform financial operations."
        ),
        model=model if model is not None else ScriptedModel(),
        tools=[],
    )


def create_finance_agent_with_subagent(
    analysis_model: ScriptedModel | None = None,
) -> Agent:
    """
    Create a Finance Agent configuration with one specialist.

    Preserve the original Finance Agent's tools, instructions,
    model, and approval configuration.

    The specialist is exposed through the SDK's agent-as-tool
    interface.
    """

    specialist = create_analysis_subagent(
        model=analysis_model,
    )

    analysis_tool = specialist.as_tool(
        tool_name="analyze_customer_information",
        tool_description=(
            "Analyze supplied customer information and "
            "return a concise read-only summary. "
            "This tool cannot modify financial records."
        ),
    )

    return Agent(
        name=finance_agent.name,
        instructions=finance_agent.instructions,
        model=finance_agent.model,
        tools=[
            *finance_agent.tools,
            analysis_tool,
        ],
    )