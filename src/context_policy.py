from dataclasses import dataclass


@dataclass
class ContextPolicy:
    recent_message_limit: int = 10
    max_memories: int = 5
    include_skill_references: bool = False