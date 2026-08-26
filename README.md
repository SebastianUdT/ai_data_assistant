# AI Data Assistant — Stage 1

A learning project built to understand the foundations behind modern AI agents before relying on production frameworks.

Stage 1 covers agent loops, tools, context, memory, MCP, skills, subagents, harnesses, validation, and real Agent SDK concepts.

## Architecture

```text
                         USER
                           |
                           v
                         AGENT
                           |
              +------------+------------+
              |                         |
              v                         v
       CONTEXT ENGINEERING          CONTROL FLOW
              |                         |
      +-------+-------+             Graph / Loop
      |       |       |                 |
      v       v       v                 v
Conversation Memory  Skills           MODEL
              |                         |
              +------------+------------+
                           |
                   +-------+-------+
                   |               |
                   v               v
                 TOOLS         SUBAGENTS
                   |
             +-----+-----+
             |           |
             v           v
           Local        MCP
             |           |
             +-----+-----+
                   |
                   v
                RESULT
                   |
                   v
              VALIDATION
              /        \
           PASS        FAIL
            |            |
            v            v
           USER       FEEDBACK
                         |
                         +----> AGENT

Why This Architecture?

The project separates responsibilities so each part can change independently:

Model decides what to do.
Agent orchestrates execution.
Tools / MCP provide capabilities.
Context Policy controls what the model receives.
Memory stores and retrieves durable information.
Skills provide reusable procedures.
Subagents isolate specialist work.
Harness / Validators control and verify execution.
Graph / State make the execution loop explicit and bounded.
Main Files
Agent
agent.py — Main orchestration and agent loop.
agent_context.py — Conversation and runtime context.
agent_state.py — Current execution state.
agent_graph.py — Agent graph nodes and routing.
agent_nodes.py — Model and tool node execution.
agent_model.py — Agent response structures.
Models and Requests
model.py — Model interface used by the Agent.
model_request.py — Structured input sent to a model.
fake_model.py — Deterministic model used for local development.
test_model.py — Simple model used by tests.
request_builder.py — Builds the final model request.
Context
conversation.py — Stores conversation messages.
context_builder.py — Builds textual context.
context_policy.py — Controls message, memory, and skill context limits.
summarizer.py — Compresses older conversation information.
Memory
memory.py — Basic memory abstraction.
semantic_memory.py — Structured long-term semantic memory.
memory_context.py — Formats retrieved memories for model context.
Tools
tools.py — Example application tools.
tool_registry.py — Registers tools, schemas, and execution.
MCP
mcp_client.py — MCP client interface.
mcp_types.py — MCP tool/call/result types.
mcp_adapter.py — Converts MCP tools to Agent tool schemas.
local_mcp_client.py — Local simulated MCP client.
local_mcp_server.py — Local simulated MCP server.
stdio_mcp_client.py — Real MCP client using stdio.
real_mcp_server.py — Real MCP server using the official SDK.
Skills
skill.py — Skill definition and context.
skill_registry.py — Stores available skills.
skill_selector.py — Selects a relevant skill.
skill_reference_loader.py — Loads specific skill references.
Subagents
subagent.py — Specialist Agent wrapper.
subagent_registry.py — Stores available subagents.
subagent_selector.py — Selects a specialist.
subagent_delegator.py — Executes delegated work.
delegation_context.py — Controls context passed from parent to child.
Harness and Validation
harness.py — Higher-level execution and validation loop.
validator.py — Validation interface.
result_validator.py — Simple output validator.
command_validator.py — Runs external commands such as pytest.
Foundations
api_client.py — Synchronous HTTP client.
async_api_client.py — Async HTTP client with retries.
config.py — Shared configuration.
llm.py, model_api.py, models.py, structured_model.py — Early structured-output/model foundations.
main.py — CLI/application entry point.
Examples

examples/mcp/ contains real MCP client demonstrations.

examples/openai_agents_sdk/ contains local examples of:

Runner
Function tools
Agents as tools
Handoffs
Guardrails
RunContext
Sessions

These use deterministic local models where possible and do not require paid API calls.

Plugin Example

stage1-demo-plugin/ demonstrates a self-contained Agent Plugin containing:

plugin.json
mcp.json
server/
skills/

It shows how Skills and MCP capabilities can be packaged together.

Core Execution Flow
User message
    |
    v
Select Skill + Retrieve Memory
    |
    v
ContextPolicy
    |
    v
Build ModelRequest
    |
    v
Model
    |
    +---- final response ----> User
    |
    +---- tool call
              |
              v
        Local Tool / MCP
              |
              v
          Tool Result
              |
              +----> Model
Run

Activate the virtual environment:

.venv\Scripts\Activate.ps1

Run the application:

python -m src.main
Tests

Run the fast regression suite:

python -m pytest -q