"""
Final Stage 2 Integration Tests

Verify:
1. Persistent memory reaches the model through ContextPolicy.
2. Trusted runtime identifiers never enter model instructions.
3. The original Finance Agent is not modified.
4. The integrated runner produces an execution report.

No paid API calls.
"""

import asyncio
from types import SimpleNamespace

import production.runner as runner

from production.agent import finance_agent
from production.context import AppContext
from production.repositories.memory_repository import MemoryRepository
from production.services.memory_service import MemoryService


def test_memory_reaches_agent_without_trusted_identifiers(
    tmp_path,
    monkeypatch,
):
    repository = MemoryRepository(
        database_path=tmp_path / "finance.db",
    )

    service = MemoryService(
        repository=repository,
    )

    service.remember(
        company_id="company_001",
        user_id="user_001",
        content="Customer prefers email contact.",
    )

    monkeypatch.setattr(
        runner,
        "MemoryService",
        lambda: service,
    )

    context = SimpleNamespace(
        company_id="company_001",
        user_id="user_001",
        operation_id="secret-operation-123",
        permissions={"internal_permission"},
    )

    original_instructions = finance_agent.instructions

    agent = runner.build_agent_with_memory(context)

    assert "Customer prefers email contact." in agent.instructions

    assert "secret-operation-123" not in agent.instructions
    assert "internal_permission" not in agent.instructions

    # The original shared agent must remain unchanged.
    assert finance_agent.instructions == original_instructions

    # Existing financial approval remains mandatory.
    credit_tool = next(
        tool
        for tool in agent.tools
        if tool.name == "apply_customer_credit"
    )

    assert credit_tool.needs_approval is True


def test_runner_generates_execution_report(
    tmp_path,
    monkeypatch,
    capsys,
):
    repository = MemoryRepository(
        database_path=tmp_path / "finance.db",
    )

    service = MemoryService(
        repository=repository,
    )

    monkeypatch.setattr(
        runner,
        "MemoryService",
        lambda: service,
    )

    # This test does not execute financial tools.
    # It verifies the application integration boundary.
    context = SimpleNamespace(
        company_id="company_001",
        user_id="user_001",
        operation_id="test-operation-001",
    )

    monkeypatch.setattr(
        runner,
        "build_context",
        lambda: context,
    )

    fake_result = SimpleNamespace(
        interruptions=[],
        new_items=[],
        final_output="Integration completed.",
    )

    async def fake_run(*args, **kwargs):
        return fake_result

    monkeypatch.setattr(
        runner.Runner,
        "run",
        fake_run,
    )

    response = asyncio.run(
        runner.run_finance_agent(
            "Test the integrated application."
        )
    )

    output = capsys.readouterr().out

    assert response == "Integration completed."
    assert "Execution report:" in output
    assert "completed" in output