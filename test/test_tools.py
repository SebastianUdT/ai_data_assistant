from src.tool_registry import Tool, ToolRegistry
from src.tools import get_customer_balance


def test_tool_schema():
    def example_tool(
        name: str,
        age: int,
    ) -> str:
        return f"Hello {name}, age {age}"

    tool = Tool(
        name="example_tool",
        description="Say hello to someone.",
        function=example_tool,
    )

    schema = tool.schema()

    assert schema["name"] == "example_tool"

    assert (
        schema["description"]
        == "Say hello to someone."
    )

    assert (
        schema["parameters"]["name"]["type"]
        == "string"
    )

    assert (
        schema["parameters"]["name"]["required"]
        is True
    )

    assert (
        schema["parameters"]["age"]["type"]
        == "integer"
    )

    assert (
        schema["parameters"]["age"]["required"]
        is True
    )

def test_tool_registry_returns_tool_error():
    registry = ToolRegistry()

    registry.register(
        name="get_customer_balance",
        description=(
            "Get the current balance "
            "for a customer."
        ),
        function=get_customer_balance,
    )

    result = registry.execute(
        name="get_customer_balance",
        arguments={
            "customer_id": "unknown",
        },
    )

    assert result == {
        "error": "Customer not found: unknown",
        "tool": "get_customer_balance",
    }
def test_tool_registry_returns_schemas():
    registry = ToolRegistry()

    registry.register(
        name="get_customer_balance",
        description="Get the current balance for a customer.",
        function=get_customer_balance,
    )

    schemas = registry.schemas()

    assert len(schemas) == 1

    assert schemas[0]["name"] == "get_customer_balance"

    assert (
        schemas[0]["description"]
        == "Get the current balance for a customer."
    )

    assert (
        schemas[0]["parameters"]["customer_id"]["type"]
        == "string"
    )

    assert (
        schemas[0]["parameters"]["customer_id"]["required"]
        is True
    )    
def test_tool_schema_contains_parameters():
    registry = ToolRegistry()

    def get_balance(
        customer_id: str,
    ) -> dict:
        return {
            "balance": 2500.0,
        }

    registry.register(
        name="get_balance",
        description="Get the customer's balance.",
        function=get_balance,
    )

    schemas = registry.schemas()

    assert schemas == [
        {
            "name": "get_balance",
            "description": "Get the customer's balance.",
            "parameters": {
                "customer_id": {
                    "type": "string",
                    "required": True,
                }
            },
        }
    ]    
def test_registry_executes_registered_tool():
    registry = ToolRegistry()

    def get_balance(
        customer_id: str,
    ) -> dict:
        return {
            "customer_id": customer_id,
            "balance": 2500.0,
        }

    registry.register(
        name="get_balance",
        description="Get the customer's balance.",
        function=get_balance,
    )

    result = registry.execute(
        name="get_balance",
        arguments={
            "customer_id": "customer_001",
        },
    )

    assert result == {
        "customer_id": "customer_001",
        "balance": 2500.0,
    }    
def test_registry_rejects_unknown_tool():
    registry = ToolRegistry()

    try:
        registry.execute(
            name="does_not_exist",
            arguments={},
        )
        assert False
    except ValueError as error:
        assert str(error) == (
            "Unknown tool: does_not_exist"
        )    