from pydantic import BaseModel


class Customer(BaseModel):
    name: str
    email: str
    purchase_amount: float


def ask_llm(prompt: str) -> dict:
    """
    Simulates an LLM returning structured data.
    """

    if "customer" in prompt.lower():
        return {
            "name": "John",
            "email": "john@example.com",
            "purchase_amount": 350,
        }

    return {
        "message": "I don't have enough information to answer that."
    }


def parse_customer(data: dict) -> Customer:
    return Customer.model_validate(data)