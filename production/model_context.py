"""
Model Context

PURPOSE
-------
Represent information intentionally exposed to the language model.

IMPORTANT
---------
Model context and runtime context are different trust boundaries.

Runtime context contains trusted application capabilities:

    services
    permissions
    authenticated identity
    operation IDs

Model context contains only information we deliberately want the
language model to know.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModelContext:
    """
    Structured information intentionally available to the model.

    Keeping this explicit makes accidental context leakage easier
    to detect and test.
    """

    company_name: str | None = None

    customer_information: dict = field(
        default_factory=dict
    )

    conversation_history: list[str] = field(
        default_factory=list
    )

    additional_information: dict = field(
        default_factory=dict
    )

    def to_prompt_text(self) -> str:
        """
        Convert structured model context into text that can be supplied
        to the model.

        We keep formatting simple for now. Production systems can later
        replace this with richer message construction if needed.
        """

        sections: list[str] = []

        if self.company_name:
            sections.append(
                f"Company: {self.company_name}"
            )

        if self.customer_information:
            sections.append(
                "Customer information:\n"
                f"{self.customer_information}"
            )

        if self.conversation_history:
            history = "\n".join(
                self.conversation_history
            )

            sections.append(
                "Recent conversation:\n"
                f"{history}"
            )

        if self.additional_information:
            sections.append(
                "Additional information:\n"
                f"{self.additional_information}"
            )

        return "\n\n".join(sections)