from typing import Any


def get_customer_balance(
    customer_id: str,
) -> dict[str, Any]:
    customers = {
        "customer_001": {
            "name": "Sebastian",
            "balance": 2500.00,
        },
        "customer_002": {
            "name": "Maria",
            "balance": 1800.00,
        },
    }

    customer = customers.get(customer_id)

    if customer is None:
        raise ValueError(
            f"Customer not found: {customer_id}"
        )

    return customer


def get_customer_invoice(
    customer_id: str,
) -> dict[str, Any]:
    invoices = {
        "customer_001": {
            "invoice_id": "INV-001",
            "amount": 1800.00,
        },
        "customer_002": {
            "invoice_id": "INV-002",
            "amount": 1200.00,
        },
    }

    invoice = invoices.get(customer_id)

    if invoice is None:
        raise ValueError(
            f"Invoice not found: {customer_id}"
        )

    return invoice