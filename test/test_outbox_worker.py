"""
Outbox Worker Tests

PURPOSE
-------
Test guarantees unique to the worker layer.

The projector already has dedicated tests for:

    - audit projection
    - idempotent delivery
    - crash before ACK
    - retry safety

Therefore this file intentionally stays small.
"""

from pathlib import Path

from production.outbox_worker import (
    OutboxWorker,
    OutboxWorkerConfig,
)
from production.repositories.audit_repository import (
    AuditRepository,
)
from production.repositories.customer_repository import (
    CustomerRepository,
)
from production.services.audit_service import (
    AUDIT_SUCCEEDED,
)
from production.services.outbox_projector import (
    OutboxProjector,
)


# =====================================================================
# FACTORY
# =====================================================================


def build_worker(
    database_path: Path,
    *,
    batch_size: int = 100,
) -> tuple[
    OutboxWorker,
    CustomerRepository,
    AuditRepository,
]:

    customer_repository = (
        CustomerRepository(
            database_path=database_path
        )
    )

    audit_repository = AuditRepository(
        database_path=database_path
    )

    projector = OutboxProjector(
        customer_repository=(
            customer_repository
        ),
        audit_repository=(
            audit_repository
        ),
    )

    worker = OutboxWorker(
        projector=projector,
        config=OutboxWorkerConfig(
            batch_size=batch_size,
            poll_interval_seconds=0,
            error_retry_seconds=0,
        ),
    )

    return (
        worker,
        customer_repository,
        audit_repository,
    )


# =====================================================================
# RUN ONCE
# =====================================================================


def test_worker_run_once_processes_pending_event(
    tmp_path: Path,
) -> None:

    (
        worker,
        customer_repository,
        audit_repository,
    ) = build_worker(
        tmp_path / "finance.db"
    )

    customer_repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    result = (
        customer_repository
        .apply_credit_adjustment_idempotent(
            operation_id="operation-001",
            user_id="user_001",
            company_id="company_001",
            customer_id="customer_001",
            amount=500.0,
        )
    )

    assert result is not None

    # Before worker:
    #
    # business transaction committed,
    # but audit projection has not happened.

    assert (
        audit_repository
        .get_events_for_operation(
            "operation-001"
        )
        == []
    )

    assert (
        len(
            customer_repository
            .get_pending_outbox_events()
        )
        == 1
    )

    processed = worker.run_once()

    assert processed == 1

    # After worker:
    #
    # durable business event became durable audit history.

    history = (
        audit_repository
        .get_events_for_operation(
            "operation-001"
        )
    )

    assert len(history) == 1

    assert (
        history[0].status
        == AUDIT_SUCCEEDED
    )

    assert (
        customer_repository
        .get_pending_outbox_events()
        == []
    )


# =====================================================================
# BATCH SIZE
# =====================================================================


def test_worker_respects_batch_size(
    tmp_path: Path,
) -> None:

    (
        worker,
        customer_repository,
        audit_repository,
    ) = build_worker(
        tmp_path / "finance.db",
        batch_size=1,
    )

    customer_repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    customer_repository.apply_credit_adjustment_idempotent(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=100.0,
    )

    customer_repository.apply_credit_adjustment_idempotent(
        operation_id="operation-002",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=100.0,
    )

    # Two events are pending.

    assert (
        len(
            customer_repository
            .get_pending_outbox_events()
        )
        == 2
    )

    # batch_size=1

    assert worker.run_once() == 1

    assert (
        len(
            customer_repository
            .get_pending_outbox_events()
        )
        == 1
    )

    assert worker.run_once() == 1

    assert (
        customer_repository
        .get_pending_outbox_events()
        == []
    )

    assert (
        len(
            audit_repository
            .get_events_for_operation(
                "operation-001"
            )
        )
        == 1
    )

    assert (
        len(
            audit_repository
            .get_events_for_operation(
                "operation-002"
            )
        )
        == 1
    )
    