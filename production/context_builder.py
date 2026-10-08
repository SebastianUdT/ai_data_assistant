"""
Production Context Builder

PURPOSE
-------
Provide one application-level place for constructing model-visible
context.

ARCHITECTURE
------------

Application data
      ↓
ContextBuilder
      ↓
ContextPolicy
      ↓
ModelContext
      ↓
Language Model

MEMORY
------
Durable memory is stored separately.

When relevant memories are recalled, this builder converts them into
model-visible information and sends them through ContextPolicy.

Trusted memory metadata such as company_id and user_id is not exposed
to the model automatically.
"""

from production.context_policy import ContextPolicy
from production.model_context import ModelContext
from production.repositories.memory_repository import (
    MemoryRecord,
)


class ContextBuilder:

    def __init__(
        self,
        *,
        policy: ContextPolicy,
    ) -> None:

        self.policy = policy

    def build(
        self,
        *,
        company_name: str | None = None,
        customer_information: dict | None = None,
        conversation_history: list[str] | None = None,
        additional_information: dict | None = None,
        memories: list[MemoryRecord] | None = None,
    ) -> ModelContext:
        """
        Construct model-visible context through the configured policy.
        """

        additional_information = dict(
            additional_information or {}
        )

        # -------------------------------------------------------------
        # MEMORY → MODEL CONTEXT
        # -------------------------------------------------------------
        #
        # Memory ownership metadata remains trusted application data.
        #
        # Only the actual memory content is a candidate for model
        # context.

        if memories:

            additional_information[
                "memories"
            ] = [
                memory.content
                for memory in memories
            ]

        return self.policy.build_model_context(
            company_name=company_name,
            customer_information=(
                customer_information
            ),
            conversation_history=(
                conversation_history
            ),
            additional_information=(
                additional_information
            ),
        )