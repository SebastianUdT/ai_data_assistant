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
                "I am the finance specialist. "
                "The customer's balance is $2500.00."
            )
        ]
    ]
)


finance_agent = Agent(
    name="Finance Specialist",
    handoff_description=(
        "Handle customer financial questions."
    ),
    instructions=(
        "Answer financial questions clearly."
    ),
    model=finance_model,
)


triage_model = ScriptedModel(
    [
        [
            function_call(
                "transfer_to_finance_specialist",
                {},
                call_id="handoff_1",
            )
        ]
    ]
)


triage_agent = Agent(
    name="Triage Agent",
    instructions=(
        "Route financial questions "
        "to the finance specialist."
    ),
    model=triage_model,
    handoffs=[
        finance_agent,
    ],
)


result = Runner.run_sync(
    triage_agent,
    "What is my balance?",
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)


print("Final output:")
print(result.final_output)

print()
print("Last agent:")
print(result.last_agent.name)

print()
print("Triage model calls:")
print(len(triage_model.calls))

print()
print("Finance model calls:")
print(len(finance_model.calls))

triage_model.assert_complete()
finance_model.assert_complete()