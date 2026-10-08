"""
Production Finance Boundary Tests

PURPOSE
-------
Test the deterministic tool/application boundary independently from
the Agents SDK.

This file intentionally does NOT retest guarantees already covered by:

    test_customer_repository.py
        database persistence and atomic mutation

    test_idempotency.py
        exactly-once mutation and replay semantics

    test_outbox.py
        transactional outbox atomicity

    test_outbox_projector.py
        SUCCEEDED projection and crash/retry safety

Here we focus only on behavior unique to the tool/application boundary:

    - authorization
    - trusted runtime operation identity
    - successful tool → service execution
    - business-error translation
    - FAILED audit ownership

IMPORTANT
---------
SUCCEEDED is NOT written directly by the tool anymore.

A successful mutation creates a durable outbox event. The outbox
projector owns the SUCCEEDED audit projection.
"""

from pathlib import Path

from production.context import AppContext
from production.repositories.audit_repository import (
    AuditRepository,
)
from production.repositories.customer_repository import (
    CustomerRepository,
)
from production.services.audit_service import (
    AUDIT_FAILED,
    AuditService,
)
from production.services.customer_service import (
    CustomerService,
)
from production.tools.customer_tools import (
    ADJUST_CUSTOMER_CREDIT,
    READ_CUSTOMER_BALANCE,
    execute_apply_customer_credit,
    execute_get_customer_balance,
)


# =====================================================================
# FACTORY
# =====================================================================


def build_context(
    database_path: Path,
    *,
    permissions: set[str] | None = None,
    operation_id: str | None = "test-operation-001",
) -> AppContext:

    customer_repository = CustomerRepository(
        database_path=database_path
    )

    customer_repository.add_customer(
        customer_id="customer_001",
        balance=2500.00,
    )

    customer_service = CustomerService(
        repository=customer_repository
    )

    audit_repository = AuditRepository(
        database_path=database_path
    )

    audit_service = AuditService(
        repository=audit_repository
    )

    return AppContext(
        user_id="test_user",
        company_id="test_company",
        customer_service=customer_service,
        audit_service=audit_service,
        permissions=permissions or set(),
        operation_id=operation_id,
    )


# =====================================================================
# READ AUTHORIZATION
# =====================================================================


def test_balance_read_with_permission(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db",
        permissions={
            READ_CUSTOMER_BALANCE,
        },
    )

    result = execute_get_customer_balance(
        context=context,
        customer_id="customer_001",
    )

    assert "2500.00" in result


def test_balance_read_without_permission(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db"
    )

    result = execute_get_customer_balance(
        context=context,
        customer_id="customer_001",
    )

    assert "Permission denied" in result


# =====================================================================
# SUCCESSFUL WRITE BOUNDARY
# =====================================================================


def test_credit_adjustment_with_permission(
    tmp_path: Path,
) -> None:

    database_path = (
        tmp_path / "finance.db"
    )

    context = build_context(
        database_path,
        permissions={
            ADJUST_CUSTOMER_CREDIT,
        },
        operation_id="operation-success-001",
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=500.0,
    )

    assert (
        "New balance: 2000.00"
        in result
    )

    assert (
        context.customer_service.get_balance(
            "customer_001"
        )
        == 2000.00
    )

    # Important architectural assertion:
    #
    # the tool must NOT directly create SUCCEEDED.
    # That responsibility now belongs to the outbox projector.

    history = (
        context.audit_service
        .get_operation_history(
            "operation-success-001"
        )
    )

    assert history == []


# =====================================================================
# WRITE AUTHORIZATION
# =====================================================================


def test_credit_adjustment_without_permission_is_blocked(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db",
        operation_id=(
            "operation-unauthorized-001"
        ),
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=500.0,
    )

    assert "Permission denied" in result

    assert (
        context.customer_service.get_balance(
            "customer_001"
        )
        == 2500.00
    )


# =====================================================================
# TRUSTED OPERATION ID
# =====================================================================


def test_credit_adjustment_without_operation_id_is_blocked(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db",
        permissions={
            ADJUST_CUSTOMER_CREDIT,
        },
        operation_id=None,
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=500.0,
    )

    assert (
        "Trusted operation ID is required"
        in result
    )

    assert (
        context.customer_service.get_balance(
            "customer_001"
        )
        == 2500.00
    )


# =====================================================================
# BUSINESS FAILURE + FAILED AUDIT
# =====================================================================


def test_invalid_adjustment_is_blocked_and_audited(
    tmp_path: Path,
) -> None:

    operation_id = (
        "operation-invalid-001"
    )

    context = build_context(
        tmp_path / "finance.db",
        permissions={
            ADJUST_CUSTOMER_CREDIT,
        },
        operation_id=operation_id,
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=1500.0,
    )

    assert (
        "cannot exceed 1000.00"
        in result
    )

    assert (
        context.customer_service.get_balance(
            "customer_001"
        )
        == 2500.00
    )

    history = (
        context.audit_service
        .get_operation_history(
            operation_id
        )
    )

    assert len(history) == 1

    event = history[0]

    assert event.status == AUDIT_FAILED

    assert (
        event.resource_id
        == "customer_001"
    )

    assert (
        event.details["amount"]
        == 1500.0
    )

    assert (
        event.details["error_type"]
        == "InvalidCreditAdjustmentError"
    )


# =====================================================================
# UNKNOWN CUSTOMER
# =====================================================================


def test_unknown_customer_is_reported(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db",
        permissions={
            ADJUST_CUSTOMER_CREDIT,
        },
        operation_id=(
            "operation-missing-customer-001"
        ),
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_999",
        amount=500.0,
    )

    assert (
        "Customer not found: customer_999"
        in result
    )


# =====================================================================
# IDEMPOTENCY CONFLICT AT TOOL BOUNDARY
# =====================================================================


def test_idempotency_conflict_is_reported(
    tmp_path: Path,
) -> None:

    context = build_context(
        tmp_path / "finance.db",
        permissions={
            ADJUST_CUSTOMER_CREDIT,
        },
        operation_id=(
            "operation-conflict-001"
        ),
    )

    execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=500.0,
    )

    result = execute_apply_customer_credit(
        context=context,
        customer_id="customer_001",
        amount=900.0,
    )

    assert (
        "Idempotency key was reused"
        in result
    )

    assert (
        context.customer_service.get_balance(
            "customer_001"
        )
        == 2000.00
    )