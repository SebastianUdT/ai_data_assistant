"""
Resume a Durable Finance Approval Request

PROCESS B
---------

trusted RunState
      ↓
restore original operation_id
      ↓
reconstruct services
      ↓
human review
      ├── APPROVED audit
      └── REJECTED audit
      ↓
SDK resume
      ↓
tool execution
      ↓
SUCCEEDED / FAILED audit
"""

import argparse
import asyncio
import json
from typing import Any

from agents import (
    RunConfig,
    Runner,
    RunState,
)

from production.agent import finance_agent
from production.context import AppContext
from production.services.audit_service import (
    AUDIT_APPROVED,
    AUDIT_REJECTED,
    AuditService,
)
from production.services.customer_service import CustomerService
from production.state_store import (
    delete_state,
    load_state,
)
from production.tools.customer_tools import (
    ADJUST_CUSTOMER_CREDIT,
)


# =====================================================================
# DURABLE CONTEXT
# =====================================================================


def get_serialized_context(
    state_json: dict[str, Any],
) -> dict[str, Any]:

    context_envelope = (
        state_json.get("context")
    )

    if not isinstance(
        context_envelope,
        dict,
    ):
        raise RuntimeError(
            "Stored RunState has no valid "
            "context envelope."
        )

    serialized_context = (
        context_envelope.get("context")
    )

    if not isinstance(
        serialized_context,
        dict,
    ):
        raise RuntimeError(
            "Stored RunState has no valid "
            "application context."
        )

    return serialized_context


# =====================================================================
# REBUILD LIVE DEPENDENCIES
# =====================================================================


def rebuild_context(
    state_json: dict[str, Any],
) -> AppContext:

    stored = get_serialized_context(
        state_json
    )

    user_id = stored.get("user_id")
    company_id = stored.get("company_id")
    permissions = stored.get("permissions")
    operation_id = stored.get(
        "operation_id"
    )

    if (
        not isinstance(user_id, str)
        or not user_id.strip()
    ):
        raise RuntimeError(
            "Stored workflow has no valid user_id."
        )

    if (
        not isinstance(company_id, str)
        or not company_id.strip()
    ):
        raise RuntimeError(
            "Stored workflow has no valid company_id."
        )

    if not isinstance(
        permissions,
        list,
    ):
        raise RuntimeError(
            "Stored workflow has no valid permissions."
        )

    if (
        not isinstance(operation_id, str)
        or not operation_id.strip()
    ):
        raise RuntimeError(
            "Stored workflow has no valid operation_id."
        )

    return AppContext(
        user_id=user_id,
        company_id=company_id,

        customer_service=CustomerService(),
        audit_service=AuditService(),

        permissions=set(
            permissions
        ),

        operation_id=operation_id,
    )


# =====================================================================
# AUDIT HUMAN DECISION
# =====================================================================


def record_review_decision(
    *,
    context: AppContext,
    interruption,
    approved: bool,
) -> None:

    if (
        interruption.name
        != "apply_customer_credit"
    ):
        return

    arguments = json.loads(
        interruption.arguments or "{}"
    )

    context.audit_service.record(
        operation_id=(
            context.require_operation_id()
        ),
        user_id=context.user_id,
        company_id=context.company_id,
        action=ADJUST_CUSTOMER_CREDIT,
        status=(
            AUDIT_APPROVED
            if approved
            else AUDIT_REJECTED
        ),
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
# REVIEW
# =====================================================================


def ask_for_decision(
    tool_name: str,
    arguments: str | None,
) -> bool:

    print()
    print(
        "=== PENDING ACTION ==="
    )

    print(
        f"Tool: {tool_name}"
    )

    print(
        f"Arguments: {arguments}"
    )

    answer = input(
        "Approve? [y/N]: "
    )

    return (
        answer.strip().lower()
        in {"y", "yes"}
    )


# =====================================================================
# RESUME
# =====================================================================


async def resume_run(
    run_id: str,
) -> None:

    state_json = load_state(
        run_id
    )

    context = rebuild_context(
        state_json
    )

    print()
    print(
        "=== WORKFLOW RESTORED ==="
    )

    print(
        f"Trusted operation ID: "
        f"{context.operation_id}"
    )

    state = await RunState.from_json(
        finance_agent,
        state_json,
        context_override=context,
        strict_context=True,
    )

    interruptions = (
        state.get_interruptions()
    )

    if not interruptions:

        print(
            "This run has no pending approvals."
        )
        return

    for interruption in interruptions:

        approved = ask_for_decision(
            tool_name=(
                interruption.name
                or "unknown_tool"
            ),
            arguments=(
                interruption.arguments
            ),
        )

        # -------------------------------------------------------------
        # AUDIT HUMAN DECISION
        # -------------------------------------------------------------

        record_review_decision(
            context=context,
            interruption=interruption,
            approved=approved,
        )

        if approved:

            state.approve(
                interruption
            )

            print(
                "Action approved."
            )

        else:

            state.reject(
                interruption,
                rejection_message=(
                    "The financial action was "
                    "rejected by the reviewer."
                ),
            )

            print(
                "Action rejected."
            )

    result = await Runner.run(
        finance_agent,
        state,
        run_config=RunConfig(
            tracing_disabled=True,
        ),
    )

    if result.interruptions:

        print()
        print(
            "The resumed workflow requested "
            "another approval."
        )

        print(
            "The run has NOT been deleted."
        )

        return

    delete_state(
        run_id
    )

    print()
    print(
        "=== FINAL AGENT RESPONSE ==="
    )

    print(
        result.final_output
    )


# =====================================================================
# CLI
# =====================================================================


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Approve or reject a durable "
            "finance-agent operation."
        )
    )

    parser.add_argument(
        "run_id",
        help=(
            "Server-side pending run identifier"
        ),
    )

    return parser.parse_args()


async def main() -> None:

    args = parse_args()

    await resume_run(
        args.run_id
    )


if __name__ == "__main__":
    asyncio.run(main())