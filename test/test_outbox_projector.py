"""
Outbox Projector Tests

PROVES
------

1. A committed outbox event becomes one SUCCEEDED audit event.
2. The event is marked processed only after projection.
3. Duplicate delivery does not duplicate the audit event.
4. Crash after audit INSERT but before ACK is recoverable.
"""

from pathlib import Path

import pytest

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


def build_repositories(
    database_path: Path,
) -> tuple[
    CustomerRepository,
    AuditRepository,
]:

    customer_repository = (
        CustomerRepository(
            database_path=database_path
        )
    )

    customer_repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    audit_repository = AuditRepository(
        database_path=database_path
    )

    return (
        customer_repository,
        audit_repository,
    )


def create_business_event(
    repository: CustomerRepository,
    operation_id: str,
) -> None:

    result = (
        repository
        .apply_credit_adjustment_idempotent(
            operation_id=operation_id,
            user_id="user_001",
            company_id="company_001",
            customer_id="customer_001",
            amount=500.0,
        )
    )

    assert result is not None
    assert result.new_balance == 2000.0


# =====================================================================
# NORMAL PROJECTION
# =====================================================================


def test_pending_event_projects_to_audit(
    tmp_path: Path,
) -> None:

    (
        customer_repository,
        audit_repository,
    ) = build_repositories(
        tmp_path / "finance.db"
    )

    operation_id = "operation-001"

    create_business_event(
        customer_repository,
        operation_id,
    )

    projector = OutboxProjector(
        customer_repository=(
            customer_repository
        ),
        audit_repository=(
            audit_repository
        ),
    )

    processed = (
        projector.process_pending()
    )

    assert processed == 1

    history = (
        audit_repository
        .get_events_for_operation(
            operation_id
        )
    )

    assert len(history) == 1

    event = history[0]

    assert event.status == AUDIT_SUCCEEDED

    assert event.user_id == "user_001"

    assert (
        event.company_id
        == "company_001"
    )

    assert (
        event.resource_id
        == "customer_001"
    )

    assert event.details == {
        "amount": 500.0,
        "resulting_balance": 2000.0,
    }

    assert event.source_event_id is not None

    pending = (
        customer_repository
        .get_pending_outbox_events()
    )

    assert pending == []


# =====================================================================
# DUPLICATE DELIVERY
# =====================================================================


def test_duplicate_delivery_does_not_duplicate_audit(
    tmp_path: Path,
) -> None:

    (
        customer_repository,
        audit_repository,
    ) = build_repositories(
        tmp_path / "finance.db"
    )

    operation_id = "operation-001"

    create_business_event(
        customer_repository,
        operation_id,
    )

    source_event = (
        customer_repository
        .get_pending_outbox_events()
    )[0]

    # Directly project the same source event twice.
    #
    # The second delivery represents queue/job retry behavior.

    first = (
        audit_repository
        .append_projected_event(
            source_event_id=(
                source_event.event_id
            ),
            operation_id=operation_id,
            user_id="user_001",
            company_id="company_001",
            action=(
                "customer.credit.adjust"
            ),
            status=AUDIT_SUCCEEDED,
            resource_type="customer",
            resource_id="customer_001",
            details={
                "amount": 500.0,
                "resulting_balance": 2000.0,
            },
        )
    )

    second = (
        audit_repository
        .append_projected_event(
            source_event_id=(
                source_event.event_id
            ),
            operation_id=operation_id,
            user_id="user_001",
            company_id="company_001",
            action=(
                "customer.credit.adjust"
            ),
            status=AUDIT_SUCCEEDED,
            resource_type="customer",
            resource_id="customer_001",
            details={
                "amount": 500.0,
                "resulting_balance": 2000.0,
            },
        )
    )

    assert (
        first.event_id
        == second.event_id
    )

    history = (
        audit_repository
        .get_events_for_operation(
            operation_id
        )
    )

    assert len(history) == 1


# =====================================================================
# FAILURE-INJECTION PROJECTOR
# =====================================================================


class CrashBeforeAckProjector(
    OutboxProjector
):

    def _mark_processed(
        self,
        event_id: str,
        *,
        worker_id: str | None = None,
    ) -> None:

        raise RuntimeError(
            "Simulated crash before ACK."
        )


# =====================================================================
# CRASH AFTER AUDIT / BEFORE ACK
# =====================================================================


def test_crash_after_audit_insert_is_safe_to_retry(
    tmp_path: Path,
) -> None:

    (
        customer_repository,
        audit_repository,
    ) = build_repositories(
        tmp_path / "finance.db"
    )

    operation_id = "operation-crash-001"

    create_business_event(
        customer_repository,
        operation_id,
    )

    crashing_projector = (
        CrashBeforeAckProjector(
            customer_repository=(
                customer_repository
            ),
            audit_repository=(
                audit_repository
            ),
        )
    )

    # -------------------------------------------------------------
    # FIRST DELIVERY
    # -------------------------------------------------------------
    #
    # Audit succeeds.
    # ACK crashes.

    with pytest.raises(
        RuntimeError,
        match="Simulated crash",
    ):

        crashing_projector.process_pending()

    history_after_crash = (
        audit_repository
        .get_events_for_operation(
            operation_id
        )
    )

    assert (
        len(history_after_crash)
        == 1
    )

    # Source event remains pending because ACK failed.

    pending_after_crash = (
        customer_repository
        .get_pending_outbox_events()
    )

    assert (
        len(pending_after_crash)
        == 1
    )

    # -------------------------------------------------------------
    # PROCESS RESTART / RETRY
    # -------------------------------------------------------------

    healthy_projector = OutboxProjector(
        customer_repository=(
            customer_repository
        ),
        audit_repository=(
            audit_repository
        ),
    )

    processed = (
        healthy_projector
        .process_pending()
    )

    assert processed == 1

    # Same source event was delivered again, but the UNIQUE
    # source_event_id prevented a duplicate audit projection.

    final_history = (
        audit_repository
        .get_events_for_operation(
            operation_id
        )
    )

    assert len(final_history) == 1

    assert (
        final_history[0].status
        == AUDIT_SUCCEEDED
    )

    assert (
        final_history[0].event_id
        == history_after_crash[0].event_id
    )

    assert (
        customer_repository
        .get_pending_outbox_events()
        == []
    )


# =====================================================================
# REPROCESS AFTER ACK
# =====================================================================


def test_processed_event_is_not_delivered_again(
    tmp_path: Path,
) -> None:

    (
        customer_repository,
        audit_repository,
    ) = build_repositories(
        tmp_path / "finance.db"
    )

    operation_id = "operation-001"

    create_business_event(
        customer_repository,
        operation_id,
    )

    projector = OutboxProjector(
        customer_repository=(
            customer_repository
        ),
        audit_repository=(
            audit_repository
        ),
    )

    assert (
        projector.process_pending()
        == 1
    )

    assert (
        projector.process_pending()
        == 0
    )

    history = (
        audit_repository
        .get_events_for_operation(
            operation_id
        )
    )

    assert len(history) == 1