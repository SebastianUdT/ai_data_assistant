from src.models import Customer
from src.model_api import parse_customer_response
import pytest


def ask_llm(prompt: str) -> dict:
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

def test_parse_customer_response():
    data = {
        "name": "John",
        "email": "john@example.com",
        "purchase_amount": 350,
    }

    customer = parse_customer_response(data)

    assert customer.name == "John"
    assert customer.email == "john@example.com"
    assert customer.purchase_amount == 350

def test_parse_customer_response_rejects_invalid_data():
    data = {
        "name": "John",
        "email": "john@example.com",
        "purchase_amount": "hello",
    }

    with pytest.raises(ValueError):
        parse_customer_response(data)    