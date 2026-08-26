from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    key: str
    value: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class SemanticMemory:
    def __init__(
        self,
    ) -> None:
        self._entries: list[MemoryEntry] = []

    def add(
        self,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            key=key,
            value=value,
            metadata=(
                metadata
                if metadata is not None
                else {}
            ),
        )

        self._entries.append(
            entry
        )

        return entry

    def list_entries(
        self,
    ) -> list[MemoryEntry]:
        return list(
            self._entries
        )

    def search(
        self,
        query: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[MemoryEntry]:
        query_text = query.lower()

        results: list[MemoryEntry] = []

        for entry in self._entries:
            searchable_text = (
                f"{entry.key} "
                f"{entry.value}"
            ).lower()

            if query_text not in searchable_text:
                continue

            if metadata is not None:
                matches_metadata = all(
                    entry.metadata.get(key)
                    == value
                    for key, value in metadata.items()
                )

                if not matches_metadata:
                    continue

            results.append(
                entry
            )

        return results

    def update(
        self,
        key: str,
        value: str,
        metadata: dict[str, Any] | None = None,
    ) -> MemoryEntry:
        for entry in self._entries:
            if entry.key != key:
                continue

            if metadata is not None:
                matches_metadata = all(
                    entry.metadata.get(meta_key)
                    == meta_value
                    for meta_key, meta_value
                    in metadata.items()
                )

                if not matches_metadata:
                    continue

            entry.value = value

            return entry

        return self.add(
            key=key,
            value=value,
            metadata=metadata,
        )