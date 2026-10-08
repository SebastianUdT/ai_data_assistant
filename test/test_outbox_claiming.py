"""
Outbox Claiming Tests

PURPOSE
-------
Protect guarantees unique to multi-worker outbox claiming.

We do NOT repeat projector, idempotency, or transactional-outbox tests.

New guarantees:

    1. one active claim has one owner
    2. another worker cannot steal an active lease
    3. an expired lease is recoverable
    4. a non-owner cannot ACK a claimed event
"""

import time
from pathlib import Path

from production.repositories.customer_repository import (
    CustomerRepository,
)


# =====================================================================
# FACTORY
# =====================================================================


def build_repository(
    database_path: Path,
) -> CustomerRepository:

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    return repository


def create_outbox_event(
    repository: CustomerRepository,
    *,
    operation_id: str = "operation-001",
) -> None:

    result = (
        repository
        .apply_credit_adjustment_idempotent(
            operation_id=operation_id,
            user_id="user_001",
            company_id="company_001",
            customer_id="customer_001",
            amount=100.0,
        )
    )

    assert result is not None


# =====================================================================
# ACTIVE CLAIM EXCLUSION
# =====================================================================


def test_active_claim_cannot_be_claimed_by_second_worker(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    create_outbox_event(repository)

    worker_a_events = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-A",
            lease_seconds=30,
        )
    )

    worker_b_events = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-B",
            lease_seconds=30,
        )
    )

    assert len(worker_a_events) == 1

    assert (
        worker_a_events[0].claimed_by
        == "worker-A"
    )

    assert worker_b_events == []


# =====================================================================
# EXPIRED LEASE RECOVERY
# =====================================================================


def test_expired_claim_can_be_recovered_by_another_worker(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    create_outbox_event(repository)

    first_claim = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-A",
            lease_seconds=0.05,
        )
    )

    assert len(first_claim) == 1

    # Small duration is used only to deterministically demonstrate
    # lease expiry in the isolated test.

    time.sleep(0.10)

    second_claim = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-B",
            lease_seconds=30,
        )
    )

    assert len(second_claim) == 1

    assert (
        second_claim[0].event_id
        == first_claim[0].event_id
    )

    assert (
        second_claim[0].claimed_by
        == "worker-B"
    )


# =====================================================================
# ACK OWNERSHIP
# =====================================================================


def test_non_owner_cannot_ack_claimed_event(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    create_outbox_event(repository)

    claimed = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-A",
            lease_seconds=30,
        )
    )

    assert len(claimed) == 1

    event_id = claimed[0].event_id

    acknowledged = (
        repository
        .mark_outbox_event_processed(
            event_id,
            worker_id="worker-B",
        )
    )

    assert acknowledged is False

    events = (
        repository
        .get_outbox_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1

    assert (
        events[0].processed_at
        is None
    )

    assert (
        events[0].claimed_by
        == "worker-A"
    )


# =====================================================================
# OWNER ACK
# =====================================================================


def test_claim_owner_can_ack_event(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    create_outbox_event(repository)

    claimed = (
        repository
        .claim_pending_outbox_events(
            worker_id="worker-A",
            lease_seconds=30,
        )
    )

    event_id = claimed[0].event_id

    acknowledged = (
        repository
        .mark_outbox_event_processed(
            event_id,
            worker_id="worker-A",
        )
    )

    assert acknowledged is True

    events = (
        repository
        .get_outbox_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1

    event = events[0]

    assert event.processed_at is not None

    assert event.claimed_by is None

    assert event.claim_until is None