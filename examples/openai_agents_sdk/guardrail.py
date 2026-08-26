from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    RunConfig,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from agents.testing import (
    ScriptedModel,
    assistant_message,
)


@input_guardrail
async def customer_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    text = (
        input
        if isinstance(input, str)
        else str(input)
    )

    blocked = (
        "delete customer"
        in text.lower()
    )

    return GuardrailFunctionOutput(
        output_info={
            "blocked": blocked,
        },
        tripwire_triggered=blocked,
    )


model = ScriptedModel(
    [
        [
            assistant_message(
                "Request accepted."
            )
        ]
    ]
)


agent = Agent(
    name="Customer Assistant",
    instructions=(
        "Help with customer requests."
    ),
    model=model,
    input_guardrails=[
        customer_guardrail,
    ],
)


print("SAFE REQUEST")

safe_result = Runner.run_sync(
    agent,
    "Show customer information.",
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)

print(safe_result.final_output)


print()
print("BLOCKED REQUEST")

try:
    Runner.run_sync(
        agent,
        "Delete customer customer_001.",
        run_config=RunConfig(
            tracing_disabled=True,
        ),
    )

except InputGuardrailTripwireTriggered:
    print(
        "Guardrail blocked the request."
    )


print()
print("Model calls:")
print(len(model.calls))

model.assert_complete()