"""
Audit Service Tests

PURPOSE
-------
Verify the application-facing audit boundary independently from agent
and SDK behavior.
"""

from pathlib import Path

from production.repositories.audit_repository import (
    AuditRepository,
)
from production.services.audit_service import (
    AUDIT_APPROVED,
    AUDIT_REQUESTED,
    AUDIT_SUCCEEDED,
    AuditService,
)


def build_service(
    database_path: Path,
) -> AuditService:

    repository = AuditRepository(
        database_path=database_path
    )

    return AuditService(
        repository=repository
    )


# =====================================================================
# RECORD WORKFLOW
# =====================================================================


def test_record_complete_successful_workflow(
    tmp_path: Path,
) -> None:

    service = build_service(
        tmp_path / "finance.db"
    )

    operation_id = "operation-001"

    service.record(
        operation_id=operation_id,
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status=AUDIT_REQUESTED,
        resource_type="customer",
        resource_id="customer_001",
        details={
            "amount": 500.0,
        },
    )

    service.record(
        operation_id=operation_id,
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status=AUDIT_APPROVED,
        resource_type="customer",
        resource_id="customer_001",
    )

    service.record(
        operation_id=operation_id,
        user_id="user-001",
        company_id="company-001",
        action="customer.credit.adjust",
        status=AUDIT_SUCCEEDED,
        resource_type="customer",
        resource_id="customer_001",
        details={
            "resulting_balance": 2000.0,
        },
    )

    history = (
        service.get_operation_history(
            operation_id
        )
    )

    assert [
        event.status
        for event in history
    ] == [
        AUDIT_REQUESTED,
        AUDIT_APPROVED,
        AUDIT_SUCCEEDED,
    ]

    assert (
        history[0].details["amount"]
        == 500.0
    )

    assert (
        history[2]
        .details["resulting_balance"]
        == 2000.0
    )