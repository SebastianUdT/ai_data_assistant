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




# AI Data Assistant — Finance Agent Architecture

> **Status:** Stage 2 learning/reference implementation complete; **not production-ready**.  
> **Audience:** Engineering leadership, developers, and stakeholders evaluating next implementation priorities.  
> **Repository:** [SebastianUdT/ai_data_assistant](https://github.com/SebastianUdT/ai_data_assistant)  
> **Latest reported verification:** 131 pytest tests passing; GitHub push completed. These are the developer's reported local results, not a CI certification.

## 1. Executive summary

AI Data Assistant is a Python-based reference implementation of an AI agent for a small company's customer and financial workflows. It demonstrates how an agent can read customer balances, request credit adjustments, obtain human approval for sensitive actions, and record financial changes reliably.

The design separates **model decisions** from **trusted application authority**. The language model may propose a tool call, but it does not create user identity, grant permissions, assign transaction IDs, approve financial operations, or directly write to the database. Those responsibilities remain in application code.

The project currently uses the **OpenAI Agents SDK** and a **deterministic `ScriptedModel`** for most tests, allowing development without paid model API calls. It includes a local MCP demonstration, persistent SQLite-backed memory, a transactional outbox with an independent audit worker, read-only subagent delegation, and basic execution reporting.

**Decision for leadership:** This is a strong technical foundation and learning prototype, **not yet a deployable multi-tenant financial assistant**. The highest-value next work is real identity/tenant enforcement, realistic end-to-end tests, an actual model evaluation, and deployment/operations design.

## 2. System architecture

```text
                       User / CLI / application request
                                    |
                                    v
                    Trusted application entry point
                    (user/company identity, operation ID)
                                    |
                  +-----------------+------------------+
                  |                                    |
                  v                                    v
        MemoryService / SQLite                AppContext (trusted)
                  |                            identity + permissions
                  v                            services + operation ID
        ContextBuilder + ContextPolicy                 |
                  |                                    |
                  +-----------------+------------------+
                                    |
                                    v
                        OpenAI Agents SDK Agent
                         (currently ScriptedModel)
                                    |
                  +-----------------+-------------------+
                  |                 |                   |
                  v                 v                   v
           Read-only tool     Credit adjustment    Analysis subagent
                  |                 |              (no financial tools)
                  |                 v
                  |         Native SDK approval
                  |           interruption
                  |                 |
                  |          Human decision
                  |                 |
                  +-----------------+
                                    |
                                    v
                            CustomerService
                                    |
                                    v
                           CustomerRepository
                                    |
                                    v
                                  SQLite
                     customers / credit_operations
                             / outbox_events
                                    |
                                    v
                         Independent outbox worker
                        claims + leases + retries
                                    |
                                    v
                           Audit projector
                                    |
                                    v
                              audit_events

             Run result --> ExecutionReport (safe metadata)
```

This diagram combines several demonstrated paths. **Not every component is exercised together in a single real-model end-to-end test.** In particular, the local MCP demonstration is separate from the principal Finance Agent's configured financial tools.

## 3. Repository map

The following paths are based on the project structure and code interfaces established during development. They describe the intended responsibilities of each component; consult the current source for exact implementation details.

### Core application

| Path | Responsibility |
|---|---|
| `production/agent.py` | Defines `finance_agent`, the balance/credit tools, and the deterministic model configuration used in the reference implementation. |
| `production/context.py` | Defines `AppContext`: trusted `user_id`, `company_id`, permissions, services, and `operation_id`. Includes `has_permission()` and `require_operation_id()`. |
| `production/runner.py` | In-process agent execution, memory/context integration, approval interruption/resume loop, and execution reporting. |
| `production/request.py` | Starts a durable approval workflow and saves the SDK run state for later action. |
| `production/approve.py` | Resumes a previously saved workflow after a separate human approval/rejection decision. |
| `production/state_store.py` | Stores and retrieves durable agent run state for cross-process approval workflows. |
| `production/database.py` | SQLite connection/database initialization and local seed data. |
| `production/observability.py` | Builds a minimal `ExecutionReport` from SDK run results or exceptions. |

### Business logic and persistence

| Path | Responsibility |
|---|---|
| `production/tools/customer_tools.py` | SDK-facing tool adapters and permission names such as `READ_CUSTOMER_BALANCE` and `ADJUST_CUSTOMER_CREDIT`. |
| `production/services/customer_service.py` | Business operations: `get_balance(customer_id)` and `apply_credit_adjustment(...)`. |
| `production/repositories/customer_repository.py` | SQLite persistence, atomic financial mutations, operation idempotency, and transactional outbox storage. |
| `production/services/audit_service.py` | Audit lifecycle business logic. |
| `production/repositories/audit_repository.py` | Audit/outbox persistence and delivery state. |
| `production/outbox_worker.py` | Independently processes pending outbox events. |
| `production/services/outbox_projector.py` | Projects outbox events into durable audit records. |

### Model context and memory

| Path | Responsibility |
|---|---|
| `production/model_context.py` | Defines the model-visible context representation and text rendering. |
| `production/context_policy.py` | Filters allowed customer information, conversation history, and additional fields. |
| `production/context_builder.py` | Combines allowed business context and recalled memories. |
| `production/services/memory_service.py` | Validates and orchestrates remembering/recalling information. |
| `production/repositories/memory_repository.py` | Stores and retrieves memories in SQLite, scoped by company and user. |

### MCP and subagents

| Path | Responsibility |
|---|---|
| `production/mcp_servers/customer_server.py` | Local MCP stdio server exposing the read-only `get_customer_balance` tool. |
| `production/mcp_servers/check_customer_mcp.py` | Direct MCP client smoke test for discovery and execution. |
| `production/mcp_servers/customer_agent.py` | Free, deterministic simulation of an agent selecting the MCP tool; **not** a live LLM agent run. |
| `production/analysis_subagent.py` | Read-only analysis specialist registered as an agent-as-tool. |

### Tests

| Path / group | Coverage |
|---|---|
| `test/test_production_finance.py` | Finance agent and approval behavior. |
| `test/test_customer_repository.py`, `test/test_idempotency.py` | Persistence, credit operations, and repeat-request safety. |
| `test/test_audit_repository.py`, `test/test_audit_service.py` | Audit storage and service behavior. |
| `test/test_outbox.py`, `test/test_outbox_claiming.py`, `test/test_outbox_projector.py`, `test/test_outbox_worker.py` | Transactional outbox, concurrent claims/leases, projection, and worker behavior. |
| `test/test_context_engineering.py`, `test/test_production_memory.py` | Context filtering, durable memory, and tenant/user-scoped recall. |
| `test/test_production_subagents.py` | Subagent configuration and actual SDK agent-as-tool delegation with scripted models. |
| `test/test_agent_evaluation.py` | Deterministic tool-call evaluation. |
| `test/test_observability.py` | Safe execution report generation. |
| `test/test_final_stage2_integration.py` | Integration wiring; runner execution is mocked in one test. |

The repository also contains Stage 1 examples and learning utilities outside `production/`; the table focuses on the Stage 2 application.

## 4. How the main workflows operate

### 4.1 Read a customer balance

1. The application creates an `AppContext` with trusted identity and permissions.
2. The Finance Agent receives the user's request.
3. The balance tool checks the relevant application permission and delegates to `CustomerService.get_balance()`.
4. The service uses the repository to retrieve the current balance from SQLite.
5. The agent returns the result.

The local MCP example provides a **separate read-only path** to the same business service using MCP stdio transport. In local testing, the MCP client discovered `get_customer_balance` and retrieved a balance successfully. **That MCP server does not yet authenticate callers or enforce tenant-scoped access**; it must not be exposed as a public financial API.

### 4.2 Request a credit adjustment

1. The application creates a trusted `operation_id` **before** running the agent.
2. The agent may request the `apply_customer_credit` tool.
3. The SDK marks this tool as requiring human approval (`needs_approval=True`).
4. Execution pauses and exposes a pending interruption.
5. A human explicitly approves or rejects the request.
6. On approval, the existing tool/service path checks authorization and performs the credit adjustment; on rejection, the requested change does not proceed.
7. The repository uses the operation ID to make retries safe and persists an outbox event with the business mutation.
8. The independent worker later processes the event into audit records.

**Important distinction:** `production/runner.py` handles approval interactively in one process. `production/request.py`, `production/approve.py`, and `production/state_store.py` demonstrate approval **across separate processes** through serialized SDK state. A production service should select one coherent deployment workflow rather than mix both entry points arbitrarily.

### 4.3 Idempotency and audit delivery

Financial mutations and audit delivery are different operations. The project uses:

- A stable, application-assigned `operation_id` to recognize repeated financial requests.
- A **transactional outbox**, so the financial change and the intent to audit it are stored together.
- An independent worker to claim pending events.
- Atomic claims, ownership checks, and expiring leases to reduce duplicate processing across workers.
- Idempotent audit projection, so replaying a delivery does not create uncontrolled duplicate audit records.

These mechanisms improve reliability under retries and worker interruptions. They do not replace operational monitoring, database backup/recovery, or real deployment testing.

### 4.4 Persistent memory and context policy

1. `MemoryService` recalls entries for the trusted `(company_id, user_id)` pair.
2. `ContextBuilder` assembles a model-visible representation.
3. `ContextPolicy` allows or excludes fields, limits conversation history, and explicitly permits memory inclusion.
4. The runner clones the Finance Agent and adds filtered reference context to that run's instructions.
5. Trusted fields such as permissions and `operation_id` remain in `AppContext`, not the prompt.

**Security limitation:** Retrieved memory is untrusted text. The current implementation labels it as reference data and warns the model not to follow embedded instructions. This is useful for the prototype but **is not a complete prompt-injection defense**. Real deployments should enforce data access independently of model instructions, apply data minimization, and evaluate malicious-memory scenarios.

### 4.5 Read-only subagent

`production/analysis_subagent.py` creates a specialist agent with **no financial tools** and exposes it to the Finance Agent through the SDK's `as_tool()` mechanism. A scripted runtime test demonstrates parent → specialist → parent execution. The specialist is for summarizing supplied information, not for granting approval or changing balances.

### 4.6 Observability

`production/observability.py` builds an `ExecutionReport` containing execution status, tool names, tool-call count, and an exception **type** on failure. It intentionally omits prompts, raw tool arguments, customer identifiers, financial amounts, and raw exception messages.

The report is generated at the application boundary; **there is no centralized logging, durable trace store, alerting system, or monitoring dashboard yet**.

## 5. Security model and trust boundaries

| Concern | Current approach | What production still needs |
|---|---|---|
| Identity | Trusted `AppContext` holds user/company identity | Real authentication and trusted identity propagation from the host system |
| Authorization | Permission checks in the application/tool path | Verified per-customer/per-tenant access control, role management, negative security tests |
| Sensitive actions | SDK-native human approval for credit tool | Authenticated approver identity, durable decision audit, reviewer UI/policy |
| Retry safety | Trusted operation IDs and repository idempotency | End-to-end correlation across services and operational retry policies |
| Audit reliability | Transactional outbox, worker, idempotent projection | Monitoring, recovery playbooks, retention policies, reconciliation |
| Model context | Explicit `ContextPolicy` and trusted/runtime separation | Stronger injection resistance, privacy review, access-controlled retrieval |
| MCP | Local read-only stdio demonstration | Caller authentication, tenant authorization, safe error mapping, deployment controls |
| Secrets | No API key required for scripted tests; `.env` ignored | Managed secrets, rotation, environment separation |
| Financial data | SQLite reference implementation | Monetary decimal/integer representation and financial validation review; production database strategy |

**Do not deploy the sample `build_context()` identity or its demonstration permissions as an authentication mechanism.** It uses fixed example identities for local learning.

## 6. Testing and evidence

At the Stage 2 checkpoint, the developer reported:

```text
131 passed in 5.70s
OPENAI_API_KEY is not set, skipping trace export
```

The API-key message is expected for a scripted/no-paid-API test run. The tests cover authorization/approval behavior, database mutations, idempotency, audit/outbox logic, memory scoping, MCP communication (via a separate local smoke test), subagent delegation, evaluations, observability, and integration wiring.

**Interpret these results carefully:**

- Most agent scenarios use `ScriptedModel`, which determines responses/tool calls in advance. This validates integration mechanics **not actual LLM reasoning quality**.
- The final integration tests include a mocked `Runner.run()` boundary. They are **not** one full end-to-end real-model financial transaction.
- The deterministic evaluation demonstrates whether a selected tool appears in the SDK execution items; it does not estimate a model's real-world tool-selection accuracy.
- Passing local tests does not imply security certification, compliance, scalability, or deployment readiness.

### Run the tests

From the repository root, using the project's activated Python virtual environment:

```powershell
python -m pytest -q
```

### Local MCP smoke test

```powershell
python -m production.mcp_servers.check_customer_mcp
```

This launches the MCP server over stdio, discovers its tool, and invokes it against the local database. The sample customer and resulting balance depend on the local database state. MCP SDK versions matter: the current example uses the **MCP 1.x** `FastMCP` interface; the 2.x API differs.

### Run the integrated scripted runner

```powershell
python -m production.runner
```

The runner's sample request is a **credit adjustment**. It may prompt for approval and, if approved, **change local SQLite financial data**. Use only disposable test data and understand the requested amount before approving. This is not a harmless read-only smoke test.

### Local data and secrets

The project ignores `.venv/`, `.env`, Python caches, `*.db`, and `production/data/` through `.gitignore`. The SQLite file is generated locally and should not be committed. Keep approval state files, secrets, and any real customer information out of Git as well; verify ignored/untracked files before committing.

## 7. Implemented vs. not implemented

| Capability | Current status | Notes |
|---|---|---|
| SDK agent with business tools | **Implemented** | Deterministic/scripted model in development |
| Trusted runtime identity/permissions | **Prototype implemented** | Identity supplied by sample application, not a real login system |
| Native HITL for credit adjustments | **Implemented and tested** | Both in-process and separate-process demonstrations |
| Idempotent SQLite credit mutation | **Implemented and tested** | Review financial numeric types before real money use |
| Transactional outbox and audit worker | **Implemented and tested** | No production monitoring/recovery operations yet |
| Context policy and persistent memory | **Implemented and tested** | Filtered memories reach a cloned agent in integration tests |
| Local MCP server/client | **Implemented and smoke-tested** | Read-only, local stdio, no production auth |
| Read-only analysis subagent | **Implemented and tested** | Scripted delegation; no financial tools |
| Deterministic evaluations | **Implemented** | Not a benchmark of live LLM quality |
| Safe execution summaries | **Implemented** | Not centrally collected or stored |
| Real LLM behavior evaluation | **Not done** | Requires model provider or other real model setup |
| Production authentication / tenant authorization | **Not done** | Required before access to real customer data |
| Deployment, CI/CD, backups, monitoring | **Not done** | Local development prototype |
| Production-grade MCP endpoint | **Not done** | Local proof of concept only |
| UI for staff/approvers | **Not done** | CLI / scripted workflows currently |
| External CRM, ERP, messaging integrations | **Not done** | No real company system connected |
| Automated memory extraction or vector search | **Not done** | Current memory is explicit SQLite storage/retrieval |
| Load testing, SLOs, security review | **Not done** | Needed for production planning |

## 8. Proposed implementation roadmap for a real company

These are **recommendations**, not claims that the features already exist.

### Priority 0 — Choose the real business use case

Define the actual workflow (for example, read-only customer support, internal finance assistance, or approval-controlled account changes), data owners, expected users, success criteria, and acceptable risk. **A read-only pilot is the lowest-risk starting point.**

### Priority 1 — Security and data correctness (before live financial access)

1. Connect real authentication and derive `user_id`/`company_id` from a trusted server-side identity source.
2. Enforce tenant/customer authorization in every data-access path, including MCP and subagents.
3. Use authenticated approval decisions and record who approved what and when.
4. Review monetary storage (`REAL`/float in the prototype), currency/rounding rules, limits, and reconciliation; prefer appropriate exact representations for real financial amounts.
5. Define privacy rules, data retention, secrets handling, and prompt-injection tests.

### Priority 2 — Real workflow and model validation

1. Connect one actual business data source in a nonproduction environment.
2. Test with a real model using a curated evaluation set, including wrong-tool, unauthorized, missing-data, and adversarial cases.
3. Run an end-to-end workflow across request, approval, mutation, outbox, and audit with realistic data and failure injection.
4. Add a safe reviewer interface or integrate approvals into the company's existing system.

### Priority 3 — Operations and deployment

1. Add CI to run tests automatically and enforce safe release gates.
2. Select a production data store, migrations, backups, and recovery strategy.
3. Add structured logs/metrics, trace correlation, alerting, and operational dashboards.
4. Define deployment environments, incident response, load limits, and rollback procedures.

### Optional / later

- Vector search or semantic memory **only if** the data size and retrieval needs justify it.
- Remote MCP servers and additional SaaS integrations **only when** a specific workflow requires them.
- More subagents, orchestration graphs, and distributed queues **only if** a simple workflow becomes insufficient.
- Web/chat UI, voice, multilingual support, and automated reporting based on user demand.

## 9. Suggested demo for stakeholders

A short demonstration can show the architecture without risking live money:

1. Run `python -m pytest -q` to show the local regression suite.
2. Run `python -m production.mcp_servers.check_customer_mcp` to show local MCP discovery and a read-only customer lookup.
3. Walk through the scripted approval tests and the `request.py` / `approve.py` flow rather than approving a real credit change in a shared database.
4. Show `ExecutionReport` and explain why tool arguments and customer details are excluded.
5. Review the roadmap above and select **one real-world pilot workflow**.

## 10. Technical notes and known boundaries

- Language/runtime: Python 3.13 in the developer environment.
- Core agent framework: OpenAI Agents SDK; development scenarios primarily use `ScriptedModel`.
- Persistence: SQLite, with a local database under `production/data/`.
- MCP demonstration: Python MCP SDK v1-compatible `FastMCP`, stdio transport.
- Testing: pytest; 131 passing tests reported at the final Stage 2 checkpoint.
- Git: Stage 2 committed and pushed to GitHub. The repository is the source of truth for the exact current implementation.
- Documentation scope: This README was prepared from the development walkthrough, shared file paths, method signatures, and reported test results. **It has not been verified against a fresh clone of the pushed repository**; validate commands, current file names, and dependencies against the repository before treating this as operational documentation.

---

**Bottom line:** The project demonstrates a layered, approval-controlled finance-agent architecture with meaningful local reliability tests. The next milestone should be **one secure, measurable pilot using real company requirements**, not additional infrastructure for its own sake.
