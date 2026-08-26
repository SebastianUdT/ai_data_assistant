from dataclasses import dataclass, field
from typing import Any


@dataclass
class Skill:
    name: str
    description: str
    instructions: str

    references: dict[str, str] = field(
        default_factory=dict
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def list_references(
        self,
    ) -> list[str]:
        return list(
            self.references.keys()
        )

    def get_reference(
        self,
        name: str,
    ) -> str:
        try:
            return self.references[name]
        except KeyError:
            raise ValueError(
                f"Unknown skill reference: {name}"
            )

    def build_context(
        self,
        include_references: bool = True,
    ) -> str:
        sections = [
            f"SKILL: {self.name}",
            (
                "DESCRIPTION:\n"
                f"{self.description}"
            ),
            (
                "INSTRUCTIONS:\n"
                f"{self.instructions}"
            ),
        ]

        if (
            include_references
            and self.references
        ):
            reference_lines = []

            for name, content in self.references.items():
                reference_lines.append(
                    f"[{name}]\n"
                    f"{content}"
                )

            sections.append(
                "REFERENCES:\n"
                + "\n\n".join(
                    reference_lines
                )
            )

        return "\n\n".join(
            sections
        )