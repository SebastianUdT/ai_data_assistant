"""
Customer Repository Tests

PURPOSE
-------
Test the persistence boundary independently from:

- agents
- tools
- permissions
- HITL


IMPORTANT
---------
The repository is also responsible for atomic persistence operations.

That means concurrency-sensitive mutations deserve tests at this layer.
"""

from concurrent.futures import (
    ThreadPoolExecutor,
)
from pathlib import Path

from production.repositories.customer_repository import (
    CustomerRepository,
)


# =====================================================================
# INSERT + READ
# =====================================================================


def test_add_and_read_customer(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path
        / "repository.db"
    )

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_test",
        balance=900.00,
    )

    assert (
        repository.get_balance(
            "customer_test"
        )
        == 900.00
    )


# =====================================================================
# MISSING CUSTOMER
# =====================================================================


def test_missing_customer_returns_none(
    tmp_path: Path,
) -> None:

    repository = CustomerRepository(
        database_path=(
            tmp_path
            / "repository.db"
        )
    )

    assert (
        repository.get_balance(
            "missing_customer"
        )
        is None
    )


# =====================================================================
# DIRECT UPDATE
# =====================================================================


def test_set_balance_persists_update(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path
        / "repository.db"
    )

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_test",
        balance=900.00,
    )

    updated = repository.set_balance(
        customer_id="customer_test",
        balance=700.00,
    )

    assert updated is True

    second_repository = CustomerRepository(
        database_path=database_path
    )

    assert (
        second_repository.get_balance(
            "customer_test"
        )
        == 700.00
    )


# =====================================================================
# DIRECT UPDATE — MISSING
# =====================================================================


def test_set_balance_missing_customer_returns_false(
    tmp_path: Path,
) -> None:

    repository = CustomerRepository(
        database_path=(
            tmp_path
            / "repository.db"
        )
    )

    updated = repository.set_balance(
        customer_id="missing_customer",
        balance=500.00,
    )

    assert updated is False


# =====================================================================
# ATOMIC CREDIT ADJUSTMENT
# =====================================================================


def test_atomic_credit_adjustment(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path
        / "repository.db"
    )

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_test",
        balance=1000.00,
    )

    new_balance = (
        repository.apply_credit_adjustment(
            customer_id="customer_test",
            amount=200.00,
        )
    )

    assert new_balance == 800.00

    assert (
        repository.get_balance(
            "customer_test"
        )
        == 800.00
    )


# =====================================================================
# ATOMIC CREDIT — MISSING CUSTOMER
# =====================================================================


def test_atomic_credit_adjustment_missing_customer(
    tmp_path: Path,
) -> None:

    repository = CustomerRepository(
        database_path=(
            tmp_path
            / "repository.db"
        )
    )

    result = (
        repository.apply_credit_adjustment(
            customer_id="missing_customer",
            amount=200.00,
        )
    )

    assert result is None


# =====================================================================
# CONCURRENT MUTATIONS
# =====================================================================


def test_concurrent_credit_adjustments_do_not_lose_updates(
    tmp_path: Path,
) -> None:
    """
    Simulate multiple workers modifying the same customer.

    Starting balance:

        1000

    Ten workers each subtract:

        10

    Correct final balance:

        900

    A read-modify-write implementation could lose updates.

    Our SQL mutation:

        balance = balance - ?

    operates against the database's current value.
    """

    database_path = (
        tmp_path
        / "concurrent.db"
    )

    repository = CustomerRepository(
        database_path=database_path
    )

    repository.add_customer(
        customer_id="customer_test",
        balance=1000.00,
    )

    def apply_adjustment() -> None:

        worker_repository = (
            CustomerRepository(
                database_path=database_path
            )
        )

        worker_repository.apply_credit_adjustment(
            customer_id="customer_test",
            amount=10.00,
        )

    with ThreadPoolExecutor(
        max_workers=5
    ) as executor:

        futures = [
            executor.submit(
                apply_adjustment
            )
            for _ in range(10)
        ]

        # IMPORTANT:
        # Calling result() propagates exceptions from worker threads.
        #
        # Without this, a concurrency test could appear successful even
        # though workers actually failed.

        for future in futures:
            future.result()

    final_repository = CustomerRepository(
        database_path=database_path
    )

    assert (
        final_repository.get_balance(
            "customer_test"
        )
        == 900.00
    )