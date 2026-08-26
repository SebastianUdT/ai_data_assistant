from agents import (
    Agent,
    RunConfig,
    Runner,
)
from agents.decorators import tool
from agents.testing import (
    ScriptedModel,
    assistant_message,
    function_call,
)


@tool
def get_customer_balance(
    customer_id: str,
) -> str:
    """Get the current balance for a customer."""

    balances = {
        "customer_001": 2500.00,
        "customer_002": 1800.00,
    }

    balance = balances.get(
        customer_id
    )

    if balance is None:
        return (
            f"Customer not found: "
            f"{customer_id}"
        )

    return (
        f"Customer {customer_id} "
        f"has a balance of {balance:.2f}"
    )


model = ScriptedModel(
    [
        [
            function_call(
                "get_customer_balance",
                {
                    "customer_id": "customer_001",
                },
                call_id="call_1",
            )
        ],
        [
            assistant_message(
                "Customer customer_001 "
                "has a balance of 2500.00."
            )
        ],
    ]
)


agent = Agent(
    name="Finance Assistant",
    instructions=(
        "Help users with customer "
        "financial information."
    ),
    model=model,
    tools=[
        get_customer_balance,
    ],
)


result = Runner.run_sync(
    agent,
    (
        "What is the balance for "
        "customer_001?"
    ),
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)


print("Final output:")
print(result.final_output)

print()
print("Model calls:")
print(len(model.calls))
print()
print("Recorded model calls:")

for index, call in enumerate(
    model.calls,
    start=1,
):
    print()
    print(f"--- MODEL CALL {index} ---")
    print(call)
model.assert_complete()
