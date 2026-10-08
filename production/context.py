"""
Production Runtime Context

PURPOSE
-------
Trusted application state and dependencies for one agent execution.

MODEL CONTEXT vs RUNTIME CONTEXT
--------------------------------
The LLM may receive business information deliberately exposed to it.

AppContext instead contains trusted runtime data:

- authenticated user
- company / tenant
- permissions
- operation identity
- business services
- audit services

These values are controlled by application code, not by the model.
"""

from dataclasses import dataclass, field

from production.services.audit_service import AuditService
from production.services.customer_service import CustomerService


@dataclass
class AppContext:
    """
    Trusted runtime dependencies for one agent workflow.
    """

    user_id: str
    company_id: str

    customer_service: CustomerService
    audit_service: AuditService

    permissions: set[str] = field(
        default_factory=set
    )

    operation_id: str | None = None

    # =================================================================
    # AUTHORIZATION
    # =================================================================

    def has_permission(
        self,
        permission: str,
    ) -> bool:

        return permission in self.permissions

    # =================================================================
    # TRUSTED OPERATION IDENTITY
    # =================================================================

    def require_operation_id(
        self,
    ) -> str:
        """
        Consequential writes fail closed when workflow identity is
        missing.

        We deliberately do NOT generate an ID here because retries and
        durable resumes must reuse the original operation ID.
        """

        if (
            self.operation_id is None
            or not self.operation_id.strip()
        ):
            raise RuntimeError(
                "Trusted operation ID is required "
                "for this write operation."
            )

        return self.operation_id