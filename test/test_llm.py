import pytest
from pydantic import ValidationError

from src.models import Customer
from src.structured_model import parse_customer


def test_parse_customer():
    data = {
        "name": "John",
        "email": "john@example.com",
        "purchase_amount": 350,
    }

    customer = parse_customer(data)

    assert isinstance(customer, Customer)
    assert customer.name == "John"
    assert customer.email == "john@example.com"
    assert customer.purchase_amount == 350


def test_invalid_customer():
    data = {
        "name": "John",
        "email": "john@example.com",
        "purchase_amount": "hello",
    }

    with pytest.raises(ValidationError):
        parse_customer(data)