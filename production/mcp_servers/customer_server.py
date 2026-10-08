"""
Customer MCP Server

Exposes customer balance information through MCP.

Architecture:
MCP Client -> MCP Server -> CustomerService -> Repository -> SQLite
"""

from mcp.server.fastmcp import FastMCP

from production.repositories.customer_repository import CustomerRepository
from production.services.customer_service import CustomerService


mcp = FastMCP("Customer Finance")


@mcp.tool()
def get_customer_balance(customer_id: str) -> str:
    """
    Retrieve a customer's current balance.

    Read-only operation.
    """

    service = CustomerService(
        repository=CustomerRepository()
    )

    try:
        # Use the actual method provided by CustomerService.
        balance = service.get_balance(customer_id)

    except Exception as error:
        # For this local exercise, surface the error.
        # Do not expose internal exception details in production.
        raise RuntimeError(
            "Unable to retrieve customer balance"
        ) from error

    return (
        f"Customer {customer_id} "
        f"has a balance of {balance:.2f}"
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")