"""
Production Memory Tests

PURPOSE
-------
Protect the minimum durable-memory architecture.

We test the behavior that matters:

    store
      ↓
    durable database
      ↓
    retrieve
      ↓
    context policy
      ↓
    model context

We also verify tenant/user isolation.
"""

from pathlib import Path

from production.context_builder import (
    ContextBuilder,
)
from production.context_policy import (
    ContextPolicy,
)
from production.repositories.memory_repository import (
    MemoryRepository,
)
from production.services.memory_service import (
    MemoryService,
)


def build_memory_service(
    database_path: Path,
) -> MemoryService:

    repository = MemoryRepository(
        database_path=database_path
    )

    return MemoryService(
        repository=repository
    )


# =====================================================================
# DURABLE MEMORY → MODEL CONTEXT
# =====================================================================


def test_memory_can_be_recalled_into_model_context(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path / "finance.db"
    )

    # -------------------------------------------------------------
    # RUN 1
    # -------------------------------------------------------------
    #
    # Store information durably.

    first_service = build_memory_service(
        database_path
    )

    first_service.remember(
        company_id="company_001",
        user_id="user_001",
        content=(
            "Customer prefers email contact."
        ),
    )

    # -------------------------------------------------------------
    # RUN 2
    # -------------------------------------------------------------
    #
    # New repository/service instances simulate another application
    # run using the same durable database.

    second_service = build_memory_service(
        database_path
    )

    memories = second_service.recall(
        company_id="company_001",
        user_id="user_001",
    )

    assert len(memories) == 1

    policy = ContextPolicy(
        allowed_additional_fields={
            "memories",
        },
    )

    builder = ContextBuilder(
        policy=policy,
    )

    context = builder.build(
        company_name="Example Company",
        memories=memories,
    )

    assert context.additional_information == {
        "memories": [
            "Customer prefers email contact."
        ]
    }

    assert (
        "Customer prefers email contact."
        in context.to_prompt_text()
    )


# =====================================================================
# OWNERSHIP ISOLATION
# =====================================================================


def test_memory_is_isolated_by_company_and_user(
    tmp_path: Path,
) -> None:

    service = build_memory_service(
        tmp_path / "finance.db"
    )

    service.remember(
        company_id="company_001",
        user_id="user_001",
        content="Company 1 private memory.",
    )

    service.remember(
        company_id="company_002",
        user_id="user_002",
        content="Company 2 private memory.",
    )

    memories = service.recall(
        company_id="company_001",
        user_id="user_001",
    )

    assert len(memories) == 1

    assert (
        memories[0].content
        == "Company 1 private memory."
    )


# =====================================================================
# CONTEXT POLICY CAN BLOCK MEMORY
# =====================================================================


def test_context_policy_can_block_recalled_memory(
    tmp_path: Path,
) -> None:

    service = build_memory_service(
        tmp_path / "finance.db"
    )

    service.remember(
        company_id="company_001",
        user_id="user_001",
        content="Sensitive remembered information.",
    )

    memories = service.recall(
        company_id="company_001",
        user_id="user_001",
    )

    # "memories" is NOT allowlisted.

    policy = ContextPolicy()

    builder = ContextBuilder(
        policy=policy,
    )

    context = builder.build(
        memories=memories,
    )

    assert (
        "memories"
        not in context.additional_information
    )

    assert (
        "Sensitive remembered information."
        not in context.to_prompt_text()
    )