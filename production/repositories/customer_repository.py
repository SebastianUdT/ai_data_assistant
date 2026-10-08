"""
Customer Repository

PURPOSE
-------
Own persistence for customer financial data, idempotency records,
and the transactional outbox.

The repository is the correct place for concurrency guarantees because
those guarantees must be enforced by the database, not by the agent,
tool, service, or worker process.
"""

import json
import sqlite3
import uuid

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from production.database import DATABASE_PATH


# =====================================================================
# RESULTS
# =====================================================================


@dataclass(frozen=True)
class CreditAdjustmentResult:
    new_balance: float
    already_processed: bool


@dataclass(frozen=True)
class OutboxEvent:
    event_id: str
    operation_id: str
    event_type: str
    payload: dict
    created_at: str
    processed_at: str | None
    claimed_by: str | None
    claim_until: str | None


# =====================================================================
# REPOSITORY
# =====================================================================


class CustomerRepository:

    def __init__(
        self,
        database_path: Path | str | None = None,
    ) -> None:

        self.database_path = Path(
    database_path
    if database_path is not None
    else DATABASE_PATH
)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    # =================================================================
    # CONNECTION
    # =================================================================

    def _connect(self) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        return connection

    # =================================================================
    # SCHEMA
    # =================================================================

    def _initialize_database(self) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    balance REAL NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS credit_operations (
                    operation_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    resulting_balance REAL NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox_events (
                    event_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    processed_at TEXT,
                    claimed_by TEXT,
                    claim_until TEXT
                )
                """
            )

            # ---------------------------------------------------------
            # DEVELOPMENT MIGRATION
            # ---------------------------------------------------------
            #
            # Existing development databases may have been created
            # before worker leases existed.
            #
            # For a real production database we would use a migration
            # framework rather than schema inspection at startup.

            columns = {
                row["name"]
                for row in connection.execute(
                    """
                    PRAGMA table_info(outbox_events)
                    """
                ).fetchall()
            }

            if "claimed_by" not in columns:

                connection.execute(
                    """
                    ALTER TABLE outbox_events
                    ADD COLUMN claimed_by TEXT
                    """
                )

            if "claim_until" not in columns:

                connection.execute(
                    """
                    ALTER TABLE outbox_events
                    ADD COLUMN claim_until TEXT
                    """
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_outbox_pending
                ON outbox_events(
                    processed_at,
                    created_at
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_outbox_operation_id
                ON outbox_events(operation_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_outbox_claim
                ON outbox_events(
                    processed_at,
                    claim_until,
                    created_at
                )
                """
            )

    # =================================================================
    # CUSTOMER CRUD
    # =================================================================

    def add_customer(
        self,
        *,
        customer_id: str,
        balance: float,
    ) -> None:

        with self._connect() as connection:

            connection.execute(
                """
                INSERT OR IGNORE INTO customers (
                    customer_id,
                    balance
                )
                VALUES (?, ?)
                """,
                (
                    customer_id,
                    balance,
                ),
            )

    def get_balance(
        self,
        customer_id: str,
    ) -> float | None:

        with self._connect() as connection:

            row = connection.execute(
                """
                SELECT balance
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

        if row is None:
            return None

        return float(row["balance"])

    def set_balance(
        self,
        *,
        customer_id: str,
        balance: float,
    ) -> bool:

        with self._connect() as connection:

            cursor = connection.execute(
                """
                UPDATE customers
                SET balance = ?
                WHERE customer_id = ?
                """,
                (
                    balance,
                    customer_id,
                ),
            )

        return cursor.rowcount == 1

    # =================================================================
    # SIMPLE ATOMIC MUTATION
    # =================================================================

    def apply_credit_adjustment(
        self,
        *,
        customer_id: str,
        amount: float,
    ) -> float | None:

        with self._connect() as connection:

            cursor = connection.execute(
                """
                UPDATE customers
                SET balance = balance - ?
                WHERE customer_id = ?
                """,
                (
                    amount,
                    customer_id,
                ),
            )

            if cursor.rowcount == 0:
                return None

            row = connection.execute(
                """
                SELECT balance
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

        if row is None:
            return None

        return float(row["balance"])

    # =================================================================
    # TRANSACTIONAL OUTBOX INSERT
    # =================================================================

    def _insert_outbox_event(
        self,
        connection: sqlite3.Connection,
        *,
        operation_id: str,
        event_type: str,
        payload: dict,
    ) -> str:
        """
        Insert using the CALLER'S transaction.

        CRITICAL:
        This method must not create its own connection or commit.

        Business mutation + idempotency record + outbox event must
        succeed or fail as one transaction.
        """

        event_id = uuid.uuid4().hex

        created_at = self._utc_now()

        connection.execute(
            """
            INSERT INTO outbox_events (
                event_id,
                operation_id,
                event_type,
                payload_json,
                created_at,
                processed_at,
                claimed_by,
                claim_until
            )
            VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL)
            """,
            (
                event_id,
                operation_id,
                event_type,
                json.dumps(payload),
                created_at,
            ),
        )

        return event_id

    # =================================================================
    # IDEMPOTENT BUSINESS MUTATION
    # =================================================================

    def apply_credit_adjustment_idempotent(
        self,
        *,
        operation_id: str,
        user_id: str,
        company_id: str,
        customer_id: str,
        amount: float,
    ) -> CreditAdjustmentResult | None:

        connection = self._connect()

        try:

            # BEGIN IMMEDIATE prevents competing writers from both
            # passing the idempotency check before either writes.

            connection.execute(
                "BEGIN IMMEDIATE"
            )

            existing = connection.execute(
                """
                SELECT
                    customer_id,
                    amount,
                    resulting_balance
                FROM credit_operations
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()

            if existing is not None:

                if (
                    existing["customer_id"]
                    != customer_id
                    or float(existing["amount"])
                    != float(amount)
                ):
                    raise ValueError(
                        "Idempotency key was reused "
                        "with different operation data."
                    )

                connection.commit()

                return CreditAdjustmentResult(
                    new_balance=float(
                        existing[
                            "resulting_balance"
                        ]
                    ),
                    already_processed=True,
                )

            cursor = connection.execute(
                """
                UPDATE customers
                SET balance = balance - ?
                WHERE customer_id = ?
                """,
                (
                    amount,
                    customer_id,
                ),
            )

            if cursor.rowcount == 0:

                connection.rollback()

                return None

            row = connection.execute(
                """
                SELECT balance
                FROM customers
                WHERE customer_id = ?
                """,
                (customer_id,),
            ).fetchone()

            if row is None:

                connection.rollback()

                return None

            new_balance = float(
                row["balance"]
            )

            connection.execute(
                """
                INSERT INTO credit_operations (
                    operation_id,
                    customer_id,
                    amount,
                    resulting_balance
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    operation_id,
                    customer_id,
                    amount,
                    new_balance,
                ),
            )

            # The durable event is self-contained.
            #
            # The projector should not need to reconstruct actor or
            # tenant identity from another audit stream.

            self._insert_outbox_event(
                connection,
                operation_id=operation_id,
                event_type=(
                    "customer.credit.adjusted"
                ),
                payload={
                    "user_id": user_id,
                    "company_id": company_id,
                    "customer_id": customer_id,
                    "amount": amount,
                    "resulting_balance": (
                        new_balance
                    ),
                },
            )

            connection.commit()

            return CreditAdjustmentResult(
                new_balance=new_balance,
                already_processed=False,
            )

        except Exception:

            connection.rollback()

            raise

        finally:

            connection.close()

    # =================================================================
    # OUTBOX READS
    # =================================================================

    def get_outbox_events_for_operation(
        self,
        operation_id: str,
    ) -> list[OutboxEvent]:

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM outbox_events
                WHERE operation_id = ?
                ORDER BY created_at, event_id
                """,
                (operation_id,),
            ).fetchall()

        return [
            self._row_to_outbox_event(row)
            for row in rows
        ]

    def get_pending_outbox_events(
        self,
        *,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        """
        Non-claiming read.

        Kept for deterministic inspection/projector tests.

        The real multi-worker execution path must use
        claim_pending_outbox_events().
        """

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT *
                FROM outbox_events
                WHERE processed_at IS NULL
                ORDER BY created_at, event_id
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            self._row_to_outbox_event(row)
            for row in rows
        ]

    # =================================================================
    # ATOMIC WORKER CLAIM
    # =================================================================

    def claim_pending_outbox_events(
        self,
        *,
        worker_id: str,
        lease_seconds: float,
        limit: int = 100,
    ) -> list[OutboxEvent]:
        """
        Atomically claim a batch for one worker.

        Eligible events are:

            - not processed
            - never claimed, OR
            - their previous lease expired

        BEGIN IMMEDIATE serializes competing SQLite writers around the
        SELECT + UPDATE claim operation.

        This prevents two workers from successfully claiming the same
        active event.
        """

        if not worker_id.strip():
            raise ValueError(
                "worker_id is required."
            )

        if lease_seconds <= 0:
            raise ValueError(
                "lease_seconds must be greater than zero."
            )

        if limit <= 0:
            return []

        now = datetime.now(timezone.utc)

        now_text = now.isoformat()

        claim_until = (
            now
            + timedelta(
                seconds=lease_seconds
            )
        ).isoformat()

        connection = self._connect()

        try:

            connection.execute(
                "BEGIN IMMEDIATE"
            )

            rows = connection.execute(
                """
                SELECT event_id
                FROM outbox_events
                WHERE
                    processed_at IS NULL
                    AND (
                        claimed_by IS NULL
                        OR claim_until IS NULL
                        OR claim_until <= ?
                    )
                ORDER BY created_at, event_id
                LIMIT ?
                """,
                (
                    now_text,
                    limit,
                ),
            ).fetchall()

            event_ids = [
                row["event_id"]
                for row in rows
            ]

            if not event_ids:

                connection.commit()

                return []

            placeholders = ",".join(
                "?"
                for _ in event_ids
            )

            connection.execute(
                f"""
                UPDATE outbox_events
                SET
                    claimed_by = ?,
                    claim_until = ?
                WHERE
                    event_id IN ({placeholders})
                    AND processed_at IS NULL
                    AND (
                        claimed_by IS NULL
                        OR claim_until IS NULL
                        OR claim_until <= ?
                    )
                """,
                (
                    worker_id,
                    claim_until,
                    *event_ids,
                    now_text,
                ),
            )

            # Read back only rows actually owned by this worker.

            claimed_rows = connection.execute(
                f"""
                SELECT *
                FROM outbox_events
                WHERE
                    event_id IN ({placeholders})
                    AND processed_at IS NULL
                    AND claimed_by = ?
                    AND claim_until = ?
                ORDER BY created_at, event_id
                """,
                (
                    *event_ids,
                    worker_id,
                    claim_until,
                ),
            ).fetchall()

            connection.commit()

            return [
                self._row_to_outbox_event(row)
                for row in claimed_rows
            ]

        except Exception:

            connection.rollback()

            raise

        finally:

            connection.close()

    # =================================================================
    # ACK
    # =================================================================

    def mark_outbox_event_processed(
        self,
        event_id: str,
        *,
        worker_id: str | None = None,
    ) -> bool:
        """
        Mark an event processed.

        Production worker path:
            worker_id is supplied and only the current claim owner may
            acknowledge the event.

        Direct deterministic projector tests:
            worker_id may be omitted.

        The compatibility path is intentionally isolated here rather
        than weakening claim ownership in the worker.
        """

        processed_at = self._utc_now()

        with self._connect() as connection:

            if worker_id is None:

                cursor = connection.execute(
                    """
                    UPDATE outbox_events
                    SET
                        processed_at = ?,
                        claimed_by = NULL,
                        claim_until = NULL
                    WHERE
                        event_id = ?
                        AND processed_at IS NULL
                    """,
                    (
                        processed_at,
                        event_id,
                    ),
                )

            else:

                cursor = connection.execute(
                    """
                    UPDATE outbox_events
                    SET
                        processed_at = ?,
                        claimed_by = NULL,
                        claim_until = NULL
                    WHERE
                        event_id = ?
                        AND processed_at IS NULL
                        AND claimed_by = ?
                    """,
                    (
                        processed_at,
                        event_id,
                        worker_id,
                    ),
                )

        return cursor.rowcount == 1

    # =================================================================
    # HELPERS
    # =================================================================

    @staticmethod
    def _utc_now() -> str:

        return datetime.now(
            timezone.utc
        ).isoformat()

    @staticmethod
    def _row_to_outbox_event(
        row: sqlite3.Row,
    ) -> OutboxEvent:

        return OutboxEvent(
            event_id=row["event_id"],
            operation_id=(
                row["operation_id"]
            ),
            event_type=row["event_type"],
            payload=json.loads(
                row["payload_json"]
            ),
            created_at=row["created_at"],
            processed_at=row["processed_at"],
            claimed_by=row["claimed_by"],
            claim_until=row["claim_until"],
        )