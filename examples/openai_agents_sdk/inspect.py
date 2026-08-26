from agents import Agent, RunConfig, set_tracing_disabled


set_tracing_disabled(True)


agent = Agent(
    name="Stage 1 Assistant",
    instructions=(
        "You are a helpful assistant."
    ),
)


config = RunConfig(
    tracing_disabled=True,
)


print("Agent name:")
print(agent.name)

print()
print("Instructions:")
print(agent.instructions)

print()
print("Tools:")
print(agent.tools)

print()
print("Handoffs:")
print(agent.handoffs)

print()
print("Run config:")
print(config)