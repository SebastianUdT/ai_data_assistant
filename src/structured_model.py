from pydantic import ValidationError

from src.models import Customer


def get_customer_data() -> dict:
    return {
        "name": "John",
        "email": "john@example.com",
        "purchase_amount": "hello",
    }


def parse_customer(data: dict) -> Customer:
    return Customer.model_validate(data)


def get_validated_customer() -> Customer | None:
    try:
        data = get_customer_data()
        return parse_customer(data)

    except ValidationError as error:
        print("Invalid customer data:")
        print(error)
        return None