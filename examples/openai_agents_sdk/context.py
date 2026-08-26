from dataclasses import dataclass

from agents import (
    Agent,
    RunConfig,
    RunContextWrapper,
    Runner,
    function_tool,
)
from agents.testing import (
    ScriptedModel,
    assistant_message,
    function_call,
)


@dataclass
class CustomerContext:
    customer_id: str
    company: str


@function_tool
def get_customer_info(
    context: RunContextWrapper[CustomerContext],
) -> str:
    customer = context.context

    return (
        f"Customer {customer.customer_id} "
        f"belongs to {customer.company}."
    )


model = ScriptedModel(
    [
        [
            function_call(
                "get_customer_info",
                {},
                call_id="context_call",
            )
        ],
        [
            assistant_message(
                "Customer customer_001 "
                "belongs to ACME."
            )
        ],
    ]
)


agent = Agent[CustomerContext](
    name="Customer Assistant",
    instructions=(
        "Help with customer information."
    ),
    model=model,
    tools=[
        get_customer_info,
    ],
)


context = CustomerContext(
    customer_id="customer_001",
    company="ACME",
)


result = Runner.run_sync(
    agent,
    "Which company does this customer belong to?",
    context=context,
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)


print("Final output:")
print(result.final_output)

print()
print("Application context:")
print(context)

print()
print("Model calls:")
print(len(model.calls))

model.assert_complete()