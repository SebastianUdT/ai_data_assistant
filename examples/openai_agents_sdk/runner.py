from agents import (
    Agent,
    RunConfig,
    Runner,
)
from agents.testing import (
    ScriptedModel,
    assistant_message,
)


model = ScriptedModel(
    [
        [
            assistant_message(
                "Hello from the real Agents SDK runner."
            )
        ]
    ]
)


agent = Agent(
    name="Stage 1 Assistant",
    instructions=(
        "You are a helpful assistant."
    ),
    model=model,
)


result = Runner.run_sync(
    agent,
    "Hello",
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)


print("Final output:")
print(result.final_output)

print()
print("Model calls:")
print(len(model.calls))

model.assert_complete()