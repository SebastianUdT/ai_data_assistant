"""
Create a Durable Agent Approval Request

PROCESS A
---------

Application creates trusted workflow identity
        ↓
Agent proposes sensitive action
        ↓
SDK interrupts for approval
        ↓
REQUESTED audit event
        ↓
RunState persisted
        ↓
process terminates
"""

import asyncio
import json
import uuid

from agents import RunConfig, Runner

from production.agent import finance_agent
from production.context import AppContext
from production.services.audit_service import (
    AUDIT_REQUESTED,
    AuditService,
)
from production.services.customer_service import CustomerService
from production.state_store import save_state
from production.tools.customer_tools import (
    ADJUST_CUSTOMER_CREDIT,
    READ_CUSTOMER_BALANCE,
)


# =====================================================================
# CONTEXT
# =====================================================================


def build_context() -> AppContext:

    operation_id = (
        f"credit-{uuid.uuid4().hex}"
    )

    return AppContext(
        user_id="user_001",
        company_id="company_001",

        customer_service=CustomerService(),
        audit_service=AuditService(),

        permissions={
            READ_CUSTOMER_BALANCE,
            ADJUST_CUSTOMER_CREDIT,
        },

        operation_id=operation_id,
    )


# =====================================================================
# DURABLE CONTEXT SERIALIZATION
# =====================================================================


def serialize_context(
    context: AppContext,
) -> dict:

    return {
        "user_id": context.user_id,
        "company_id": context.company_id,
        "permissions": sorted(
            context.permissions
        ),
        "operation_id": context.operation_id,
    }


# =====================================================================
# AUDIT REQUEST
# =====================================================================


def record_requested_events(
    context: AppContext,
    interruptions: list,
) -> None:
    """
    Record what actually reached the approval boundary.

    Tool arguments are parsed from the SDK interruption rather than
    reconstructed from the user's natural-language request.
    """

    operation_id = (
        context.require_operation_id()
    )

    for interruption in interruptions:

        if (
            interruption.name
            != "apply_customer_credit"
        ):
            continue

        arguments = json.loads(
            interruption.arguments or "{}"
        )

        context.audit_service.record(
            operation_id=operation_id,
            user_id=context.user_id,
            company_id=context.company_id,
            action=ADJUST_CUSTOMER_CREDIT,
            status=AUDIT_REQUESTED,
            resource_type="customer",
            resource_id=arguments.get(
                "customer_id"
            ),
            details={
                "amount": arguments.get(
                    "amount"
                ),
            },
        )


# =====================================================================
# REQUEST
# =====================================================================


async def main() -> None:

    context = build_context()

    print()
    print("=== WORKFLOW CREATED ===")
    print(
        f"Trusted operation ID: "
        f"{context.operation_id}"
    )

    result = await Runner.run(
        finance_agent,
        (
            "Apply a 500 credit adjustment "
            "to customer_001."
        ),
        context=context,
        run_config=RunConfig(
            tracing_disabled=True,
        ),
    )

    if not result.interruptions:

        print()
        print(
            "Run completed without "
            "requiring approval."
        )
        print(result.final_output)
        return

    # -----------------------------------------------------------------
    # AUDIT BEFORE PERSISTING THE PENDING WORKFLOW
    # -----------------------------------------------------------------

    record_requested_events(
        context,
        list(result.interruptions),
    )

    run_id = uuid.uuid4().hex

    state = result.to_state()

    state_json = state.to_json(
        context_serializer=serialize_context,
        strict_context=True,
    )

    path = save_state(
        run_id,
        state_json,
    )

    print()
    print(
        "=== APPROVAL REQUEST CREATED ==="
    )

    print(f"Run ID: {run_id}")

    print(
        f"Trusted operation ID: "
        f"{context.operation_id}"
    )

    for interruption in (
        result.interruptions
    ):
        print()
        print(
            f"Tool: {interruption.name}"
        )
        print(
            f"Arguments: "
            f"{interruption.arguments}"
        )

    print()
    print(
        "The financial tool has NOT executed."
    )

    print(
        f"State saved to: {path}"
    )


if __name__ == "__main__":
    asyncio.run(main())