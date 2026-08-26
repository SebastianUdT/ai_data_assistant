from src.models import Customer


def ask_llm(
    prompt: str,
) -> dict:
    if "customer" in prompt.lower():
        return {
            "name": "John",
            "email": "john@example.com",
            "purchase_amount": 350,
        }

    return {
        "message": (
            "I don't have enough information "
            "to answer that."
        )
    }


def parse_customer(
    data: dict,
) -> Customer:
    return Customer.model_validate(
        data
    )