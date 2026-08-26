from dataclasses import dataclass, field
from typing import Any


@dataclass
class ModelRequest:
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] = field(
        default_factory=list
    )