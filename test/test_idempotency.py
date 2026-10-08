"""
Idempotency Tests

PURPOSE
-------
Verify exactly-once business mutation semantics.

Trusted actor/tenant identity is now also passed into the repository
because a NEW successful operation creates a self-contained durable
outbox event.

These tests verify:

- first execution mutates once
- retry returns the original result
- replay metadata is preserved
- different operation IDs execute independently
- conflicting reuse is rejected
- concurrent duplicate execution remains safe
"""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from production.repositories.customer_repository import (
    CustomerRepository,
)
from production.services.customer_service import (
    CustomerService,
    IdempotencyConflictError,
)


# =====================================================================
# FACTORY
# =====================================================================


def build_service(
    database_path: Path,
) -> CustomerService:

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    return CustomerService(
        repository=repository
    )


# =====================================================================
# FIRST EXECUTION
# =====================================================================


def test_credit_operation_executes_once(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    outcome = service.apply_credit_adjustment(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=500.0,
    )

    assert outcome.new_balance == 2000.00
    assert outcome.replayed is False

    assert (
        service.get_balance(
            "customer_001"
        )
        == 2000.00
    )


# =====================================================================
# RETRY
# =====================================================================


def test_same_operation_id_does_not_execute_twice(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    first = service.apply_credit_adjustment(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=500.0,
    )

    second = service.apply_credit_adjustment(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=500.0,
    )

    assert first.new_balance == 2000.00
    assert second.new_balance == 2000.00

    assert first.replayed is False
    assert second.replayed is True

    assert (
        service.get_balance(
            "customer_001"
        )
        == 2000.00
    )


# =====================================================================
# DIFFERENT OPERATIONS
# =====================================================================


def test_different_operation_ids_execute_independently(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    first = service.apply_credit_adjustment(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=500.0,
    )

    second = service.apply_credit_adjustment(
        operation_id="operation-002",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=300.0,
    )

    assert first.replayed is False
    assert second.replayed is False

    assert second.new_balance == 1700.00

    assert (
        service.get_balance(
            "customer_001"
        )
        == 1700.00
    )


# =====================================================================
# CONFLICT
# =====================================================================


def test_operation_id_cannot_be_reused_for_different_amount(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    service.apply_credit_adjustment(
        operation_id="operation-001",
        user_id="user_001",
        company_id="company_001",
        customer_id="customer_001",
        amount=500.0,
    )

    with pytest.raises(
        IdempotencyConflictError
    ):

        service.apply_credit_adjustment(
            operation_id="operation-001",
            user_id="user_001",
            company_id="company_001",
            customer_id="customer_001",
            amount=900.0,
        )

    assert (
        service.get_balance(
            "customer_001"
        )
        == 2000.00
    )


# =====================================================================
# CONCURRENT DUPLICATE
# =====================================================================


def test_concurrent_same_operation_executes_once(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    def execute():

        return service.apply_credit_adjustment(
            operation_id="operation-001",
            user_id="user_001",
            company_id="company_001",
            customer_id="customer_001",
            amount=500.0,
        )

    with ThreadPoolExecutor(
        max_workers=2
    ) as executor:

        outcomes = list(
            executor.map(
                lambda _: execute(),
                range(2),
            )
        )

    assert [
        outcome.new_balance
        for outcome in outcomes
    ] == [
        2000.00,
        2000.00,
    ]

    assert sorted(
        outcome.replayed
        for outcome in outcomes
    ) == [
        False,
        True,
    ]

    assert (
        service.get_balance(
            "customer_001"
        )
        == 2000.00
    )