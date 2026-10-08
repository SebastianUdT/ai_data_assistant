"""
Transactional Outbox Worker

PURPOSE
-------
Run the outbox projector as an independent background process.

The worker now uses database-backed expiring leases so multiple worker
processes do not actively process the same event.

Run with:

    python -m production.outbox_worker
"""

import time
import uuid

from dataclasses import dataclass

from production.repositories.audit_repository import (
    AuditRepository,
)
from production.repositories.customer_repository import (
    CustomerRepository,
)
from production.services.outbox_projector import (
    OutboxProjector,
)


# =====================================================================
# CONFIGURATION
# =====================================================================


@dataclass(frozen=True)
class OutboxWorkerConfig:

    batch_size: int = 100

    poll_interval_seconds: float = 2.0

    error_retry_seconds: float = 5.0

    # The lease must normally be comfortably longer than expected
    # processing time for one batch.
    #
    # Later we can add lease renewal for genuinely long-running work.

    lease_seconds: float = 30.0


# =====================================================================
# WORKER
# =====================================================================


class OutboxWorker:

    def __init__(
        self,
        *,
        projector: OutboxProjector,
        config: OutboxWorkerConfig | None = None,
        worker_id: str | None = None,
    ) -> None:

        self.projector = projector

        self.config = (
            config
            or OutboxWorkerConfig()
        )

        # Worker identity belongs to trusted runtime infrastructure,
        # never to the model.

        self.worker_id = (
            worker_id
            or f"worker-{uuid.uuid4().hex}"
        )

    # =================================================================
    # ONE CLAIMED BATCH
    # =================================================================

    def run_once(
        self,
    ) -> int:
        """
        Claim and process one batch.

        Only events successfully claimed by this worker are processed.
        """

        events = (
            self.projector
            .customer_repository
            .claim_pending_outbox_events(
                worker_id=self.worker_id,
                lease_seconds=(
                    self.config.lease_seconds
                ),
                limit=(
                    self.config.batch_size
                ),
            )
        )

        processed = 0

        for event in events:

            self.projector.process_event(
                event,
                worker_id=self.worker_id,
            )

            processed += 1

        return processed

    # =================================================================
    # PROCESS LOOP
    # =================================================================

    def run_forever(
        self,
    ) -> None:

        print(
            "Outbox worker started "
            f"(worker_id={self.worker_id}, "
            f"batch_size={self.config.batch_size}, "
            f"lease={self.config.lease_seconds}s, "
            f"poll="
            f"{self.config.poll_interval_seconds}s)"
        )

        try:

            while True:

                try:

                    processed = (
                        self.run_once()
                    )

                    if processed > 0:

                        print(
                            "Outbox worker processed "
                            f"{processed} event(s)."
                        )

                    time.sleep(
                        self.config
                        .poll_interval_seconds
                    )

                except Exception as error:

                    # We deliberately do NOT release the claim here.
                    #
                    # Why?
                    #
                    # A failed worker should not immediately create a
                    # hot retry loop. The lease provides bounded retry
                    # delay and eventually makes the event available
                    # to another worker.

                    print(
                        "Outbox worker batch failed: "
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                    print(
                        "Outbox worker will retry "
                        f"in "
                        f"{self.config.error_retry_seconds}s."
                    )

                    time.sleep(
                        self.config
                        .error_retry_seconds
                    )

        except KeyboardInterrupt:

            print(
                "\nOutbox worker stopped."
            )


# =====================================================================
# COMPOSITION ROOT
# =====================================================================


def build_worker() -> OutboxWorker:

    customer_repository = (
        CustomerRepository()
    )

    audit_repository = (
        AuditRepository()
    )

    projector = OutboxProjector(
        customer_repository=(
            customer_repository
        ),
        audit_repository=(
            audit_repository
        ),
    )

    return OutboxWorker(
        projector=projector
    )


# =====================================================================
# CLI
# =====================================================================


def main() -> None:

    worker = build_worker()

    worker.run_forever()


if __name__ == "__main__":
    main()