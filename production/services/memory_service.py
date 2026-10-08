"""
Production Memory Service

PURPOSE
-------
Provide the application-level interface for durable agent memory.

ARCHITECTURE
------------
Application / Agent
        ↓
MemoryService
        ↓
MemoryRepository
        ↓
SQLite

RESPONSIBILITIES
----------------
- Validate memory requests.
- Store durable memories.
- Retrieve memories belonging to a company/user.
- Keep persistence details outside agent and tool code.

Memory retrieval does not automatically expose information to the LLM.
ContextBuilder and ContextPolicy control that separately.
"""

from production.repositories.memory_repository import (
    MemoryRecord,
    MemoryRepository,
)


# =====================================================================
# MEMORY SERVICE
# =====================================================================


class MemoryService:

    def __init__(
        self,
        repository: MemoryRepository | None = None,
    ) -> None:
        """
        Dependency injection allows tests to supply an isolated
        repository and production to use the default database.
        """

        self.repository = (
            repository
            if repository is not None
            else MemoryRepository()
        )

    # =================================================================
    # REMEMBER
    # =================================================================

    def remember(
        self,
        *,
        company_id: str,
        user_id: str,
        content: str,
    ) -> MemoryRecord:
        """
        Persist durable information for one company/user.

        Ownership identifiers must come from trusted application
        context, not from untrusted model-generated arguments.
        """

        if not company_id.strip():
            raise ValueError(
                "company_id is required."
            )

        if not user_id.strip():
            raise ValueError(
                "user_id is required."
            )

        if not content.strip():
            raise ValueError(
                "Memory content cannot be empty."
            )

        return self.repository.add_memory(
            company_id=company_id,
            user_id=user_id,
            content=content.strip(),
        )

    # =================================================================
    # RECALL
    # =================================================================

    def recall(
        self,
        *,
        company_id: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryRecord]:
        """
        Retrieve recent memories belonging to one company/user.

        The repository enforces ownership filtering in SQL.

        The returned records are not automatically added to
        model-visible context.
        """

        if not company_id.strip():
            raise ValueError(
                "company_id is required."
            )

        if not user_id.strip():
            raise ValueError(
                "user_id is required."
            )

        if limit <= 0:
            return []

        return self.repository.get_memories(
            company_id=company_id,
            user_id=user_id,
            limit=limit,
        )