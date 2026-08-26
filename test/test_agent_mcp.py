from src.agent import Agent
from src.agent_model import AgentResponse
from src.local_mcp_client import LocalMCPClient
from src.local_mcp_server import LocalMCPServer
from src.model import Model
from src.model_request import ModelRequest
from src.tool_registry import ToolRegistry


class MCPTestModel(Model):
    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        for message in request.messages:
            if message.get("role") == "tool_result":
                metadata = message.get("metadata")

                if metadata is not None:
                    result = metadata.get("result")

                    if (
                        isinstance(result, dict)
                        and "balance" in result
                    ):
                        return AgentResponse(
                            content=(
                                "Your MCP balance is "
                                f"${result['balance']:.2f}."
                            )
                        )

        for tool in request.tools:
            if tool["name"] == "get_mcp_balance":
                return AgentResponse(
                    tool_name="get_mcp_balance",
                    arguments={
                        "customer_id": "customer_001",
                    },
                )

        return AgentResponse(
            content="MCP tool not available."
        )


def create_mcp_client() -> LocalMCPClient:
    registry = ToolRegistry()

    def get_mcp_balance(
        customer_id: str,
    ) -> dict:
        return {
            "customer_id": customer_id,
            "balance": 3200,
        }

    registry.register(
        name="get_mcp_balance",
        description=(
            "Get customer balance through MCP."
        ),
        function=get_mcp_balance,
    )

    server = LocalMCPServer(
        tool_registry=registry,
    )

    return LocalMCPClient(
        server=server,
    )


def test_agent_can_use_mcp_tool():
    client = create_mcp_client()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=MCPTestModel(),
        mcp_client=client,
    )

    result = agent.run(
        "What is my MCP balance?"
    )

    assert (
        result
        == "Your MCP balance is $3200.00."
    )

    messages = agent.conversation.get_messages()

    assert len(messages) == 4

    assert messages[0].role == "user"

    assert messages[1].role == "tool_call"
    assert (
        messages[1].metadata["tool_name"]
        == "get_mcp_balance"
    )

    assert messages[2].role == "tool_result"
    assert (
        messages[2].metadata["result"]["balance"]
        == 3200
    )

    assert messages[3].role == "assistant"


def test_agent_discovers_mcp_tool():
    client = create_mcp_client()

    class InspectingModel(Model):
        def __init__(self):
            self.request = None

        def generate(
            self,
            request: ModelRequest,
        ) -> AgentResponse:
            self.request = request

            return AgentResponse(
                content="Done."
            )

    model = InspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
        mcp_client=client,
    )

    agent.run("Hello")

    assert model.request is not None

    assert len(model.request.tools) == 1

    assert (
        model.request.tools[0]["name"]
        == "get_mcp_balance"
    )