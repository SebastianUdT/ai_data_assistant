from agents import (
    Agent,
    RunConfig,
    Runner,
    SQLiteSession,
)
from agents.testing import (
    ScriptedModel,
    assistant_message,
)


model = ScriptedModel(
    [
        [
            assistant_message(
                "Nice to meet you, Sebastian."
            )
        ],
        [
            assistant_message(
                "Your name is Sebastian."
            )
        ],
    ]
)


agent = Agent(
    name="Memory Assistant",
    instructions=(
        "Remember information from the "
        "conversation."
    ),
    model=model,
)


session = SQLiteSession(
    "stage1-demo-user"
)


print("RUN 1")

result_1 = Runner.run_sync(
    agent,
    "My name is Sebastian.",
    session=session,
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)

print(result_1.final_output)


print()
print("RUN 2")

result_2 = Runner.run_sync(
    agent,
    "What is my name?",
    session=session,
    run_config=RunConfig(
        tracing_disabled=True,
    ),
)

print(result_2.final_output)


print()
print("Model calls:")
print(len(model.calls))

model.assert_complete()