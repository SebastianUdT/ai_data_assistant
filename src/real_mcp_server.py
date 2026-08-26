from mcp.server import MCPServer


mcp = MCPServer(
    "stage-1-demo"
)


@mcp.tool()
def get_customer_balance(
    customer_id: str,
) -> dict:
    """Get the current balance for a customer."""

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

    customer = customers.get(
        customer_id
    )

    if customer is None:
        raise ValueError(
            f"Customer not found: {customer_id}"
        )

    return customer


@mcp.resource(
    "customer://customer_001"
)
def get_customer_profile() -> dict:
    """Get the profile for customer_001."""

    return {
        "customer_id": "customer_001",
        "name": "Sebastian",
        "account_type": "business",
    }


@mcp.prompt()
def explain_balance(
    customer_name: str,
    balance: float,
) -> str:
    """Create a prompt for explaining a customer balance."""

    return (
        f"Explain to {customer_name} "
        f"that their current balance is "
        f"${balance:.2f}. "
        "Keep the explanation short and clear."
    )


if __name__ == "__main__":
    mcp.run()