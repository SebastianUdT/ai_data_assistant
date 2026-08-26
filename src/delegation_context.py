from dataclasses import dataclass, field
from typing import Any


@dataclass
class DelegationContext:
    data: dict[str, Any] = field(
        default_factory=dict
    )

    instructions: str = ""

    def build_task(
        self,
        task: str,
    ) -> str:
        sections = [
            f"TASK:\n{task}"
        ]

        if self.instructions:
            sections.append(
                "INSTRUCTIONS:\n"
                f"{self.instructions}"
            )

        if self.data:
            data_lines = [
                f"{name}: {value}"
                for name, value in self.data.items()
            ]

            sections.append(
                "CONTEXT:\n"
                + "\n".join(data_lines)
            )

        return "\n\n".join(
            sections
        )