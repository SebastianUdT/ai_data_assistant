from agents import (
    Agent,
    RunConfig,
    Runner,
)
from agents.testing import (
    ScriptedModel,
    assistant_message,
    function_call,
)


finance_model = ScriptedModel(
    [
        [
            assistant_message(
                "The customer's financial "
                "analysis is complete."
            )
        ]
    ]
)


finance_agent = Agent(
    name="Finance Specialist",
    instructions=(
        "Handle financial analysis."
    ),
    model=finance_model,
)


finance_tool = finance_agent.as_tool(
    tool_name="finance_specialist",
    tool_description=(
        "Analyze financial questions."
    ),
)


manager_model = ScriptedModel(
    [
        [
            function_call(
                "finance_specialist",
                {
                    "input": (
                        "Analyze the customer's "
                        "financial situation."
                    )
                },
                call_id="call_finance",
            )
        ],
        [
            assistant_message(
                "The finance specialist completed "
                "the analysis successfully."
            )
        ],
    ]
)


manager_agent = Agent(
    name="Manager",
    instructions=(
        "Delegate specialist work when needed."
    ),
    model=manager_model,
    tools=[
        finance_tool,
    ],
)


result = Runner.run_sync(
    manager_agent,
    (
        "Analyze the customer's "
        "financial situation."
    ),
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)


print("Final output:")
print(result.final_output)

print()
print("Manager model calls:")
print(len(manager_model.calls))

print()
print("Finance model calls:")
print(len(finance_model.calls))

manager_model.assert_complete()
finance_model.assert_complete()