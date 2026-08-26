from mcp.server import MCPServer


mcp = MCPServer(
    "stage1-demo-plugin"
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


if __name__ == "__main__":
    mcp.run()