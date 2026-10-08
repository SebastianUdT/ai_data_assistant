"""
Customer Agent Tools

AUDIT OWNERSHIP
---------------

REQUESTED / APPROVED / REJECTED
    orchestration layer

SUCCEEDED
    transactional outbox → projector

REPLAYED
    tool execution boundary

FAILED
    tool execution boundary


WHY SUCCEEDED MOVED
-------------------

The tool must NOT directly record SUCCEEDED anymore.

The authoritative success fact is created atomically with the business
mutation inside CustomerRepository.

A projector later converts that durable outbox event into SUCCEEDED.
"""

from agents import (
    RunContextWrapper,
    function_tool,
)

from production.context import AppContext
from production.services.audit_service import (
    AUDIT_FAILED,
    AUDIT_REPLAYED,
)
from production.services.customer_service import (
    CustomerNotFoundError,
    IdempotencyConflictError,
    InvalidCreditAdjustmentError,
)


READ_CUSTOMER_BALANCE = (
    "customer.balance.read"
)

ADJUST_CUSTOMER_CREDIT = (
    "customer.credit.adjust"
)


# =====================================================================
# READ
# =====================================================================


def execute_get_customer_balance(
    context: AppContext,
    customer_id: str,
) -> str:

    if not context.has_permission(
        READ_CUSTOMER_BALANCE
    ):
        return (
            "Permission denied: "
            "customer balance access "
            "is not allowed."
        )

    try:
        balance = (
            context.customer_service
            .get_balance(customer_id)
        )

    except CustomerNotFoundError as error:
        return str(error)

    return (
        f"Customer {customer_id} "
        f"has a balance of "
        f"{balance:.2f}"
    )


# =====================================================================
# AUDIT HELPER
# =====================================================================


def _record_credit_outcome(
    *,
    context: AppContext,
    operation_id: str,
    status: str,
    customer_id: str,
    amount: float,
    details: dict | None = None,
) -> None:

    event_details = {
        "amount": amount,
    }

    if details:
        event_details.update(details)

    context.audit_service.record(
        operation_id=operation_id,
        user_id=context.user_id,
        company_id=context.company_id,
        action=ADJUST_CUSTOMER_CREDIT,
        status=status,
        resource_type="customer",
        resource_id=customer_id,
        details=event_details,
    )


# =====================================================================
# WRITE
# =====================================================================


def execute_apply_customer_credit(
    context: AppContext,
    customer_id: str,
    amount: float,
) -> str:

    # -----------------------------------------------------------------
    # AUTHORIZATION
    # -----------------------------------------------------------------

    if not context.has_permission(
        ADJUST_CUSTOMER_CREDIT
    ):
        return (
            "Permission denied: "
            "customer credit adjustments "
            "are not allowed."
        )

    # -----------------------------------------------------------------
    # TRUSTED OPERATION ID
    # -----------------------------------------------------------------

    try:
        operation_id = (
            context.require_operation_id()
        )

    except RuntimeError as error:
        return str(error)

    # -----------------------------------------------------------------
    # BUSINESS EXECUTION
    # -----------------------------------------------------------------

    try:
        outcome = (
            context.customer_service
            .apply_credit_adjustment(
                operation_id=operation_id,
                user_id=context.user_id,
                company_id=context.company_id,
                customer_id=customer_id,
                amount=amount,
            )
        )

    except (
        CustomerNotFoundError,
        InvalidCreditAdjustmentError,
        IdempotencyConflictError,
    ) as error:

        _record_credit_outcome(
            context=context,
            operation_id=operation_id,
            status=AUDIT_FAILED,
            customer_id=customer_id,
            amount=amount,
            details={
                "error": str(error),
                "error_type": (
                    type(error).__name__
                ),
            },
        )

        return str(error)

    # -----------------------------------------------------------------
    # REPLAY AUDIT
    # -----------------------------------------------------------------
    #
    # A NEW execution does NOT record SUCCEEDED here.
    #
    # Its durable success event already exists transactionally in the
    # outbox and will be projected later.

    if outcome.replayed:

        _record_credit_outcome(
            context=context,
            operation_id=operation_id,
            status=AUDIT_REPLAYED,
            customer_id=customer_id,
            amount=amount,
            details={
                "resulting_balance": (
                    outcome.new_balance
                ),
            },
        )

    return (
        f"Credit adjustment of "
        f"{amount:.2f} applied to "
        f"{customer_id}. "
        f"New balance: "
        f"{outcome.new_balance:.2f}"
    )


# =====================================================================
# SDK ADAPTERS
# =====================================================================


@function_tool
def get_customer_balance(
    ctx: RunContextWrapper[AppContext],
    customer_id: str,
) -> str:

    return execute_get_customer_balance(
        context=ctx.context,
        customer_id=customer_id,
    )


@function_tool(
    needs_approval=True
)
def apply_customer_credit(
    ctx: RunContextWrapper[AppContext],
    customer_id: str,
    amount: float,
) -> str:

    return execute_apply_customer_credit(
        context=ctx.context,
        customer_id=customer_id,
        amount=amount,
    )