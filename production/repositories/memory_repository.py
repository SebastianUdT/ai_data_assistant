"""
Production Memory Repository

PURPOSE
-------
Persist durable information that may be useful in future agent runs.

ARCHITECTURE
------------
Application / Agent
        ↓
MemoryService
        ↓
MemoryRepository
        ↓
SQLite

IMPORTANT
---------
Memory is not automatically model context.

Stored memory must pass through retrieval and ContextPolicy before
the model can see it.
"""

import sqlite3
import uuid

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from production.database import DATABASE_PATH


# =====================================================================
# MEMORY RECORD
# =====================================================================


@dataclass(frozen=True)
class MemoryRecord:
    """
    One durable memory belonging to a specific company and user.
    """

    memory_id: str
    company_id: str
    user_id: str
    content: str
    created_at: str


# =====================================================================
# MEMORY REPOSITORY
# =====================================================================


class MemoryRepository:

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
    # DATABASE CONNECTION
    # =================================================================

    def _connect(self) -> sqlite3.Connection:
        """
        Create a connection to the configured SQLite database.

        The injectable database path allows tests to use isolated
        temporary databases without touching production data.
        """

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
        """
        Create the memory table and ownership index.

        Production systems normally manage schema changes through
        migrations rather than startup initialization.
        """

        with self._connect() as connection:

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_memories_owner
                ON memories (
                    company_id,
                    user_id,
                    created_at
                )
                """
            )

    # =================================================================
    # WRITE MEMORY
    # =================================================================

    def add_memory(
        self,
        *,
        company_id: str,
        user_id: str,
        content: str,
    ) -> MemoryRecord:
        """
        Store a durable memory for one company/user.

        The caller must provide trusted ownership information.
        """

        memory_id = uuid.uuid4().hex

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:

            connection.execute(
                """
                INSERT INTO memories (
                    memory_id,
                    company_id,
                    user_id,
                    content,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    company_id,
                    user_id,
                    content,
                    created_at,
                ),
            )

        return MemoryRecord(
            memory_id=memory_id,
            company_id=company_id,
            user_id=user_id,
            content=content,
            created_at=created_at,
        )

    # =================================================================
    # READ MEMORY
    # =================================================================

    def get_memories(
        self,
        *,
        company_id: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """
        Retrieve recent memories for exactly one company/user.

        SECURITY
        --------
        Ownership filtering happens inside the SQL query.

        We never retrieve all companies' memories and filter afterward.
        """

        if limit <= 0:
            return []

        with self._connect() as connection:

            rows = connection.execute(
                """
                SELECT
                    memory_id,
                    company_id,
                    user_id,
                    content,
                    created_at
                FROM memories
                WHERE
                    company_id = ?
                    AND user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (
                    company_id,
                    user_id,
                    limit,
                ),
            ).fetchall()

        return [
            MemoryRecord(
                memory_id=row["memory_id"],
                company_id=row["company_id"],
                user_id=row["user_id"],
                content=row["content"],
                created_at=row["created_at"],
            )
            for row in rows
        ]