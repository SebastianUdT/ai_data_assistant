"""
Outbox Projector

PURPOSE
-------
Translate durable business outbox events into durable audit history.

The projector owns event interpretation and idempotent projection.

It does NOT own:

    - polling
    - worker identity
    - lease acquisition
    - process lifetime

Those belong to the worker/repository layers.
"""

from production.repositories.audit_repository import (
    AuditRepository,
)
from production.repositories.customer_repository import (
    CustomerRepository,
    OutboxEvent,
)
from production.services.audit_service import (
    AUDIT_SUCCEEDED,
)


CREDIT_ADJUSTED_EVENT = (
    "customer.credit.adjusted"
)

CREDIT_ADJUST_ACTION = (
    "customer.credit.adjust"
)


class UnsupportedOutboxEventError(
    RuntimeError
):
    pass


class OutboxProjector:

    def __init__(
        self,
        *,
        customer_repository: CustomerRepository,
        audit_repository: AuditRepository,
    ) -> None:

        self.customer_repository = (
            customer_repository
        )

        self.audit_repository = (
            audit_repository
        )

    # =================================================================
    # SIMPLE SINGLE-PROCESS PATH
    # =================================================================

    def process_pending(
        self,
        *,
        limit: int = 100,
    ) -> int:
        """
        Process pending events without worker claiming.

        This remains useful for deterministic projector tests and
        one-shot local projection.

        The standalone production worker uses claims instead.
        """

        events = (
            self.customer_repository
            .get_pending_outbox_events(
                limit=limit
            )
        )

        processed = 0

        for event in events:

            self.process_event(event)

            processed += 1

        return processed

    # =================================================================
    # EVENT PROJECTION
    # =================================================================

    def process_event(
        self,
        event: OutboxEvent,
        *,
        worker_id: str | None = None,
    ) -> None:
        """
        Project one event and acknowledge it.

        Audit insertion is idempotent by source_event_id.

        Therefore this sequence is safe:

            audit INSERT
                ↓
            crash
                ↓
            event redelivered
                ↓
            same source_event_id
                ↓
            existing audit event reused
                ↓
            ACK

        When worker_id is supplied, only the worker holding the claim
        may ACK the source event.
        """

        if (
            event.event_type
            != CREDIT_ADJUSTED_EVENT
        ):
            raise UnsupportedOutboxEventError(
                "Unsupported outbox event: "
                f"{event.event_type}"
            )

        payload = event.payload

        self.audit_repository.append_projected_event(
            source_event_id=event.event_id,
            operation_id=event.operation_id,
            user_id=payload["user_id"],
            company_id=payload["company_id"],
            action=CREDIT_ADJUST_ACTION,
            status=AUDIT_SUCCEEDED,
            resource_type="customer",
            resource_id=(
                payload["customer_id"]
            ),
            details={
                "amount": payload["amount"],
                "resulting_balance": (
                    payload[
                        "resulting_balance"
                    ]
                ),
            },
        )

        self._mark_processed(
            event.event_id,
            worker_id=worker_id,
        )

    # =================================================================
    # ACK
    # =================================================================

    def _mark_processed(
        self,
        event_id: str,
        *,
        worker_id: str | None = None,
    ) -> None:
        """
        Extracted as an intentional crash-injection seam.

        Existing projector tests can subclass this method to simulate
        a crash after audit insertion but before source ACK.
        """

        acknowledged = (
            self.customer_repository
            .mark_outbox_event_processed(
                event_id,
                worker_id=worker_id,
            )
        )

        if not acknowledged:
            raise RuntimeError(
                "Outbox event could not be "
                "acknowledged. The worker may "
                "no longer own the claim."
            )