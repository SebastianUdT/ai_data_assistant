"""
Audit Repository Tests

PURPOSE
-------
Verify that audit history is:

- persistent
- append-only
- ordered
- grouped by operation_id
- isolated between operations
"""

from pathlib import Path

from production.repositories.audit_repository import (
    AuditRepository,
)


# =====================================================================
# APPEND
# =====================================================================


def test_append_audit_event(
    tmp_path: Path,
) -> None:

    repository = AuditRepository(
        database_path=(
            tmp_path / "finance.db"
        )
    )

    event = repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
        resource_type="customer",
        resource_id="customer_001",
        details={
            "amount": 500.0,
        },
    )

    assert (
        event.operation_id
        == "operation-001"
    )

    assert (
        event.status
        == "REQUESTED"
    )

    assert (
        event.details["amount"]
        == 500.0
    )


# =====================================================================
# OPERATION HISTORY
# =====================================================================


def test_operation_history_contains_all_events(
    tmp_path: Path,
) -> None:

    repository = AuditRepository(
        database_path=(
            tmp_path / "finance.db"
        )
    )

    repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
    )

    repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="APPROVED",
    )

    repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="SUCCEEDED",
    )

    events = (
        repository
        .get_events_for_operation(
            "operation-001"
        )
    )

    assert [
        event.status
        for event in events
    ] == [
        "REQUESTED",
        "APPROVED",
        "SUCCEEDED",
    ]


# =====================================================================
# OPERATION ISOLATION
# =====================================================================


def test_operation_history_is_isolated(
    tmp_path: Path,
) -> None:

    repository = AuditRepository(
        database_path=(
            tmp_path / "finance.db"
        )
    )

    repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
    )

    repository.append_event(
        operation_id="operation-002",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
    )

    first_operation = (
        repository
        .get_events_for_operation(
            "operation-001"
        )
    )

    assert len(
        first_operation
    ) == 1

    assert (
        first_operation[0].operation_id
        == "operation-001"
    )


# =====================================================================
# PERSISTENCE
# =====================================================================


def test_audit_history_survives_new_repository_instance(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path / "finance.db"
    )

    first_repository = (
        AuditRepository(
            database_path=database_path
        )
    )

    first_repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
        details={
            "amount": 500.0,
        },
    )

    # Simulate another application/process instance.

    second_repository = (
        AuditRepository(
            database_path=database_path
        )
    )

    events = (
        second_repository
        .get_events_for_operation(
            "operation-001"
        )
    )

    assert len(events) == 1

    assert (
        events[0].details["amount"]
        == 500.0
    )


# =====================================================================
# DIFFERENT EVENTS HAVE DIFFERENT IDENTITIES
# =====================================================================


def test_each_audit_event_has_unique_event_id(
    tmp_path: Path,
) -> None:

    repository = AuditRepository(
        database_path=(
            tmp_path / "finance.db"
        )
    )

    first = repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="REQUESTED",
    )

    second = repository.append_event(
        operation_id="operation-001",
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status="APPROVED",
    )

    assert (
        first.event_id
        != second.event_id
    )