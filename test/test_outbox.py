"""
Transactional Outbox Tests

PURPOSE
-------
Prove the write-side guarantees of the transactional outbox.

We verify:

1. Successful mutation creates one self-contained durable event.
2. Idempotent retry creates no second business event.
3. Concurrent duplicate requests create one event.
4. Outbox failure rolls back the entire transaction.
"""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from production.repositories.customer_repository import (
    CustomerRepository,
)


USER_ID = "user_001"
COMPANY_ID = "company_001"


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


# =====================================================================
# SUCCESS
# =====================================================================


def test_successful_operation_creates_outbox_event(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    result = (
        repository
        .apply_credit_adjustment_idempotent(
            operation_id="operation-001",
            user_id=USER_ID,
            company_id=COMPANY_ID,
            customer_id="customer_001",
            amount=500.0,
        )
    )

    assert result is not None

    assert result.new_balance == 2000.00
    assert result.already_processed is False

    events = (
        repository
        .get_outbox_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == (
        "customer.credit.adjusted"
    )

    assert event.payload == {
        "user_id": USER_ID,
        "company_id": COMPANY_ID,
        "customer_id": "customer_001",
        "amount": 500.0,
        "resulting_balance": 2000.0,
    }

    assert event.processed_at is None


# =====================================================================
# RETRY
# =====================================================================


def test_idempotent_retry_does_not_create_second_outbox_event(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    first = (
        repository
        .apply_credit_adjustment_idempotent(
            operation_id="operation-001",
            user_id=USER_ID,
            company_id=COMPANY_ID,
            customer_id="customer_001",
            amount=500.0,
        )
    )

    second = (
        repository
        .apply_credit_adjustment_idempotent(
            operation_id="operation-001",
            user_id=USER_ID,
            company_id=COMPANY_ID,
            customer_id="customer_001",
            amount=500.0,
        )
    )

    assert first is not None
    assert second is not None

    assert first.already_processed is False
    assert second.already_processed is True

    assert (
        repository.get_balance(
            "customer_001"
        )
        == 2000.00
    )

    events = (
        repository
        .get_outbox_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1


# =====================================================================
# CONCURRENT RETRY
# =====================================================================


def test_concurrent_duplicate_operation_creates_one_outbox_event(
    tmp_path: Path,
) -> None:

    repository = build_repository(
        tmp_path / "finance.db"
    )

    def execute():

        return (
            repository
            .apply_credit_adjustment_idempotent(
                operation_id="operation-001",
                user_id=USER_ID,
                company_id=COMPANY_ID,
                customer_id="customer_001",
                amount=500.0,
            )
        )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        results = list(
            executor.map(
                lambda _: execute(),
                range(2),
            )
        )

    assert all(
        result is not None
        for result in results
    )

    assert sorted(
        result.already_processed
        for result in results
        if result is not None
    ) == [
        False,
        True,
    ]

    assert (
        repository.get_balance(
            "customer_001"
        )
        == 2000.00
    )

    events = (
        repository
        .get_outbox_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1


# =====================================================================
# FAILURE INJECTION
# =====================================================================


class FailingOutboxRepository(
    CustomerRepository
):

    def _insert_outbox_event(
        self,
        connection,
        *,
        operation_id: str,
        event_type: str,
        payload: dict,
    ) -> str:

        raise RuntimeError(
            "Simulated outbox failure."
        )


# =====================================================================
# TOTAL ROLLBACK
# =====================================================================


def test_outbox_failure_rolls_back_business_transaction(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path / "finance.db"
    )

    repository = (
        FailingOutboxRepository(
            database_path=database_path
        )
    )

    repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated outbox failure",
    ):

        repository.apply_credit_adjustment_idempotent(
            operation_id="operation-failure-001",
            user_id=USER_ID,
            company_id=COMPANY_ID,
            customer_id="customer_001",
            amount=500.0,
        )

    # Business mutation rolled back.

    assert (
        repository.get_balance(
            "customer_001"
        )
        == 2500.00
    )

    # Outbox INSERT rolled back.

    assert (
        repository
        .get_outbox_events_for_operation(
            "operation-failure-001"
        )
        == []
    )

    # Idempotency INSERT rolled back.

    with sqlite3.connect(
        database_path
    ) as connection:

        row = connection.execute(
            """
            SELECT operation_id
            FROM credit_operations
            WHERE operation_id = ?
            """,
            (
                "operation-failure-001",
            ),
        ).fetchone()

    assert row is None