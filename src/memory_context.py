from src.semantic_memory import MemoryEntry


def build_memory_context(
    memories: list[MemoryEntry],
) -> str:
    if not memories:
        return ""

    lines = []

    for memory in memories:
        lines.append(
            f"{memory.key}: {memory.value}"
        )

    return (
        "RELEVANT MEMORY:\n"
        + "\n".join(lines)
    )