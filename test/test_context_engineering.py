"""
Production Context Engineering Tests

PURPOSE
-------
Protect the boundary between application information and information
intentionally exposed to the language model.

We keep this suite small because advanced context management is outside
the current project's requirements.
"""

from production.context_builder import ContextBuilder
from production.context_policy import ContextPolicy


def test_context_policy_filters_model_visible_information():
    policy = ContextPolicy(
        max_conversation_messages=2,
        allowed_additional_fields={
            "department",
        },
    )

    builder = ContextBuilder(
        policy=policy,
    )

    context = builder.build(
        company_name="Example Company",
        customer_information={
            "customer_id": "customer_001",
            "balance": 2500,
        },
        conversation_history=[
            "old message",
            "recent message 1",
            "recent message 2",
        ],
        additional_information={
            "department": "finance",

            # Simulates information available to the application that
            # must not automatically enter model context.
            "internal_secret": (
                "DO NOT EXPOSE"
            ),
        },
    )

    assert context.company_name == (
        "Example Company"
    )

    assert context.customer_information == {
        "customer_id": "customer_001",
        "balance": 2500,
    }

    assert context.conversation_history == [
        "recent message 1",
        "recent message 2",
    ]

    assert context.additional_information == {
        "department": "finance",
    }

    prompt_text = context.to_prompt_text()

    assert "DO NOT EXPOSE" not in prompt_text
    assert "internal_secret" not in prompt_text


def test_customer_information_can_be_excluded():
    policy = ContextPolicy(
        include_customer_information=False,
    )

    builder = ContextBuilder(
        policy=policy,
    )

    context = builder.build(
        customer_information={
            "customer_id": "customer_001",
            "balance": 2500,
        },
    )

    assert context.customer_information == {}