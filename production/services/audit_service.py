"""
Audit Service

PURPOSE
-------
Provide the application-facing boundary for recording durable workflow
and execution events.

AUDIT VOCABULARY
----------------

REQUESTED
    A concrete consequential action reached the approval boundary.

APPROVED
    A human reviewer approved the action.

REJECTED
    A human reviewer rejected the action.

SUCCEEDED
    This invocation actually performed the business mutation.

REPLAYED
    The same logical operation had already succeeded earlier.
    No new business mutation occurred.

FAILED
    Execution was attempted but failed.
"""

from pathlib import Path

from production.repositories.audit_repository import (
    AuditEvent,
    AuditRepository,
)


# =====================================================================
# AUDIT STATUSES
# =====================================================================


AUDIT_REQUESTED = "REQUESTED"
AUDIT_APPROVED = "APPROVED"
AUDIT_REJECTED = "REJECTED"

AUDIT_SUCCEEDED = "SUCCEEDED"
AUDIT_REPLAYED = "REPLAYED"
AUDIT_FAILED = "FAILED"


# =====================================================================
# SERVICE
# =====================================================================


class AuditService:

    def __init__(
        self,
        repository: AuditRepository | None = None,
        *,
        database_path: Path | None = None,
    ) -> None:

        if repository is not None:
            self.repository = repository

        elif database_path is not None:
            self.repository = AuditRepository(
                database_path=database_path
            )

        else:
            self.repository = (
                AuditRepository()
            )

    # =================================================================
    # RECORD
    # =================================================================

    def record(
        self,
        *,
        operation_id: str,
        user_id: str,
        company_id: str,
        action: str,
        status: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> AuditEvent:

        return self.repository.append_event(
            operation_id=operation_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )

    # =================================================================
    # HISTORY
    # =================================================================

    def get_operation_history(
        self,
        operation_id: str,
    ) -> list[AuditEvent]:

        return (
            self.repository
            .get_events_for_operation(
                operation_id
            )
        )