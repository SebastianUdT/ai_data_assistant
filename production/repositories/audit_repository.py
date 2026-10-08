"""
Audit Repository

PURPOSE
-------
Persist append-only audit history.

PROJECTED EVENTS
----------------

Some audit records originate from durable outbox events.

For those records:

    source_event_id = outbox event_id

The database enforces uniqueness.

Therefore delivering the same outbox event multiple times does not
create multiple logical audit records.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from production.database import DATABASE_PATH


# =====================================================================
# DOMAIN RECORD
# =====================================================================


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    operation_id: str
    user_id: str
    company_id: str
    action: str
    status: str
    resource_type: str | None
    resource_id: str | None
    details: dict
    created_at: str
    source_event_id: str | None


# =====================================================================
# REPOSITORY
# =====================================================================


class AuditRepository:

    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ) -> None:

        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    # =================================================================
    # CONNECTION
    # =================================================================

    def _get_connection(
        self,
    ) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.database_path,
            timeout=10.0,
        )

        connection.row_factory = sqlite3.Row

        return connection

    # =================================================================
    # SCHEMA + MIGRATION
    # =================================================================

    def _initialize_database(
        self,
    ) -> None:

        with self._get_connection() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    company_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    source_event_id TEXT
                )
                """
            )

            # Existing development databases were created before
            # source_event_id existed. Perform a small additive migration.

            columns = connection.execute(
                """
                PRAGMA table_info(audit_events)
                """
            ).fetchall()

            column_names = {
                row["name"]
                for row in columns
            }

            if (
                "source_event_id"
                not in column_names
            ):
                connection.execute(
                    """
                    ALTER TABLE audit_events
                    ADD COLUMN source_event_id TEXT
                    """
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_audit_events_operation_id
                ON audit_events(operation_id)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_audit_events_company_id
                ON audit_events(company_id)
                """
            )

            # SQLite UNIQUE indexes allow multiple NULL values.
            #
            # Normal REQUESTED/APPROVED/etc. events therefore remain
            # append-only, while projected events receive a stable
            # source identity.

            connection.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                    idx_audit_events_source_event_id
                ON audit_events(source_event_id)
                WHERE source_event_id IS NOT NULL
                """
            )

    # =================================================================
    # NORMAL APPEND
    # =================================================================

    def append_event(
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

        return self._append(
            event_id=uuid.uuid4().hex,
            source_event_id=None,
            operation_id=operation_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
        )

    # =================================================================
    # IDEMPOTENT PROJECTED APPEND
    # =================================================================

    def append_projected_event(
        self,
        *,
        source_event_id: str,
        operation_id: str,
        user_id: str,
        company_id: str,
        action: str,
        status: str,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
    ) -> AuditEvent:
        """
        Append an audit projection idempotently.

        source_event_id is stable across delivery retries.

        If the same source event was already projected, return the
        existing audit record instead of creating another one.
        """

        with self._get_connection() as connection:

            existing = connection.execute(
                """
                SELECT
                    event_id,
                    operation_id,
                    user_id,
                    company_id,
                    action,
                    status,
                    resource_type,
                    resource_id,
                    details_json,
                    created_at,
                    source_event_id
                FROM audit_events
                WHERE source_event_id = ?
                """,
                (
                    source_event_id,
                ),
            ).fetchone()

        if existing is not None:
            return self._row_to_event(
                existing
            )

        event = AuditEvent(
            event_id=uuid.uuid4().hex,
            operation_id=operation_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            source_event_id=source_event_id,
        )

        try:

            with self._get_connection() as connection:

                connection.execute(
                    """
                    INSERT INTO audit_events (
                        event_id,
                        operation_id,
                        user_id,
                        company_id,
                        action,
                        status,
                        resource_type,
                        resource_id,
                        details_json,
                        created_at,
                        source_event_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.operation_id,
                        event.user_id,
                        event.company_id,
                        event.action,
                        event.status,
                        event.resource_type,
                        event.resource_id,
                        json.dumps(
                            event.details,
                            sort_keys=True,
                        ),
                        event.created_at,
                        event.source_event_id,
                    ),
                )

            return event

        except sqlite3.IntegrityError:
            # Another worker may have projected the same source event
            # after our initial SELECT but before our INSERT.
            #
            # The UNIQUE index is the final concurrency authority.

            with self._get_connection() as connection:

                existing = connection.execute(
                    """
                    SELECT
                        event_id,
                        operation_id,
                        user_id,
                        company_id,
                        action,
                        status,
                        resource_type,
                        resource_id,
                        details_json,
                        created_at,
                        source_event_id
                    FROM audit_events
                    WHERE source_event_id = ?
                    """,
                    (
                        source_event_id,
                    ),
                ).fetchone()

            if existing is None:
                raise

            return self._row_to_event(
                existing
            )

    # =================================================================
    # INTERNAL NORMAL INSERT
    # =================================================================

    def _append(
        self,
        *,
        event_id: str,
        source_event_id: str | None,
        operation_id: str,
        user_id: str,
        company_id: str,
        action: str,
        status: str,
        resource_type: str | None,
        resource_id: str | None,
        details: dict,
    ) -> AuditEvent:

        event = AuditEvent(
            event_id=event_id,
            operation_id=operation_id,
            user_id=user_id,
            company_id=company_id,
            action=action,
            status=status,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            created_at=datetime.now(
                timezone.utc
            ).isoformat(),
            source_event_id=source_event_id,
        )

        with self._get_connection() as connection:

            connection.execute(
                """
                INSERT INTO audit_events (
                    event_id,
                    operation_id,
                    user_id,
                    company_id,
                    action,
                    status,
                    resource_type,
                    resource_id,
                    details_json,
                    created_at,
                    source_event_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.operation_id,
                    event.user_id,
                    event.company_id,
                    event.action,
                    event.status,
                    event.resource_type,
                    event.resource_id,
                    json.dumps(
                        event.details,
                        sort_keys=True,
                    ),
                    event.created_at,
                    event.source_event_id,
                ),
            )

        return event

    # =================================================================
    # READ
    # =================================================================

    def get_events_for_operation(
        self,
        operation_id: str,
    ) -> list[AuditEvent]:

        with self._get_connection() as connection:

            rows = connection.execute(
                """
                SELECT
                    event_id,
                    operation_id,
                    user_id,
                    company_id,
                    action,
                    status,
                    resource_type,
                    resource_id,
                    details_json,
                    created_at,
                    source_event_id
                FROM audit_events
                WHERE operation_id = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (
                    operation_id,
                ),
            ).fetchall()

        return [
            self._row_to_event(row)
            for row in rows
        ]

    # =================================================================
    # MAPPING
    # =================================================================

    @staticmethod
    def _row_to_event(
        row: sqlite3.Row,
    ) -> AuditEvent:

        return AuditEvent(
            event_id=row["event_id"],
            operation_id=row["operation_id"],
            user_id=row["user_id"],
            company_id=row["company_id"],
            action=row["action"],
            status=row["status"],
            resource_type=row["resource_type"],
            resource_id=row["resource_id"],
            details=json.loads(
                row["details_json"]
            ),
            created_at=row["created_at"],
            source_event_id=row[
                "source_event_id"
            ],
        )