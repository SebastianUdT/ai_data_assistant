"""
Production Context Policy

PURPOSE
-------
Control which application information is allowed to enter model context.

WHY
---
Having data available to the application does not automatically mean
the language model should receive it.

This policy creates an explicit boundary between:

    available application data

and:

    model-visible data
"""

from dataclasses import dataclass, field

from production.model_context import ModelContext


@dataclass(frozen=True)
class ContextPolicy:
    """
    Minimum production context policy.

    More sophisticated policies can later add:

        token budgets
        summarization
        semantic retrieval
        role-based context
        sensitive-data classification

    We do not need those yet.
    """

    include_customer_information: bool = True

    max_conversation_messages: int = 6

    allowed_additional_fields: set[str] = field(
        default_factory=set
    )

    def build_model_context(
        self,
        *,
        company_name: str | None = None,
        customer_information: dict | None = None,
        conversation_history: list[str] | None = None,
        additional_information: dict | None = None,
    ) -> ModelContext:
        """
        Apply the policy and return information that may be exposed
        to the model.
        """

        customer_information = (
            customer_information or {}
        )

        conversation_history = (
            conversation_history or []
        )

        additional_information = (
            additional_information or {}
        )

        # -------------------------------------------------------------
        # CUSTOMER DATA
        # -------------------------------------------------------------

        if self.include_customer_information:
            filtered_customer_information = dict(
                customer_information
            )
        else:
            filtered_customer_information = {}

        # -------------------------------------------------------------
        # CONVERSATION
        # -------------------------------------------------------------
        #
        # Keep only the most recent messages.
        #
        # This is our minimum context-size control for now.

        if self.max_conversation_messages <= 0:
            filtered_history = []
        else:
            filtered_history = conversation_history[
                -self.max_conversation_messages:
            ]

        # -------------------------------------------------------------
        # ADDITIONAL INFORMATION
        # -------------------------------------------------------------
        #
        # Allowlist instead of blocklist.
        #
        # New fields are excluded by default until the application
        # deliberately permits them.

        filtered_additional_information = {
            key: value
            for key, value
            in additional_information.items()
            if key
            in self.allowed_additional_fields
        }

        return ModelContext(
            company_name=company_name,
            customer_information=(
                filtered_customer_information
            ),
            conversation_history=(
                filtered_history
            ),
            additional_information=(
                filtered_additional_information
            ),
        )