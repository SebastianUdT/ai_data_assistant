from src.agent import Agent, create_agent
from src.agent_graph import AgentNode
from src.agent_model import AgentResponse
from src.model_request import ModelRequest
from src.test_model import TestModel
from src.tool_registry import ToolRegistry


def test_agent_uses_tool():
    agent = create_agent()

    result = agent.run(
        "What is my balance?"
    )

    assert (
        result
        == "Your balance is $2500.00."
    )


def test_agent_uses_invoice_tool():
    agent = create_agent()

    result = agent.run(
        "What is my invoice?"
    )

    assert (
        result
        == "Your invoice is $1800.00."
    )


def test_agent_answers_without_tool():
    agent = create_agent()

    result = agent.run(
        "Hello"
    )

    assert (
        result
        == "I don't need a tool to answer that."
    )


def test_agent_can_use_multiple_tools():
    agent = create_agent()

    result = agent.run(
        "Check my balance and my invoice."
    )

    assert (
        result
        == (
            "Your balance is $2500.00 "
            "and your invoice is $1800.00."
        )
    )


def test_agent_stops_after_max_iterations():
    agent = create_agent(
        max_iterations=1
    )

    try:
        agent.run(
            "Check my balance and my invoice."
        )
        assert False
    except RuntimeError as error:
        assert (
            str(error)
            == "Agent exceeded the maximum number "
            "of iterations."
        )


def test_agent_handles_tool_error():
    agent = create_agent()

    agent.tool_registry._tools[
        "get_customer_balance"
    ].function = lambda customer_id: {
        "error": "Customer not found: unknown",
        "tool": "get_customer_balance",
    }

    result = agent.run(
        "What is my balance?"
    )

    assert (
        result
        == (
            "I couldn't complete the request "
            "because the tool returned an error: "
            "Customer not found: unknown"
        )
    )


def test_agent_stores_conversation():
    agent = create_agent()

    agent.run(
        "What is my balance?"
    )

    messages = agent.conversation.get_messages()

    assert len(messages) == 4

    assert messages[0].role == "user"

    assert (
        messages[0].content
        == "What is my balance?"
    )

    assert messages[1].role == "tool_call"

    assert (
        messages[1].metadata["tool_name"]
        == "get_customer_balance"
    )

    assert (
        messages[1].metadata["arguments"]
        == {
            "customer_id": "customer_001",
        }
    )

    assert messages[2].role == "tool_result"

    assert (
        messages[2].metadata["tool_name"]
        == "get_customer_balance"
    )

    assert (
        messages[2].metadata["result"]["balance"]
        == 2500
    )

    assert messages[3].role == "assistant"

    assert (
        messages[3].content
        == "Your balance is $2500.00."
    )


def test_agent_stores_tool_call():
    agent = create_agent()

    agent.run(
        "What is my balance?"
    )

    messages = agent.conversation.get_messages()

    assert len(messages) == 4

    assert messages[0].role == "user"
    assert messages[1].role == "tool_call"

    assert (
        messages[1].metadata["tool_name"]
        == "get_customer_balance"
    )

    assert (
        messages[1].metadata["arguments"]
        == {
            "customer_id": "customer_001",
        }
    )

    assert messages[2].role == "tool_result"

    assert (
        messages[2].metadata["tool_name"]
        == "get_customer_balance"
    )

    assert (
        messages[2].metadata["result"]["balance"]
        == 2500
    )

    assert messages[3].role == "assistant"


def test_agent_can_use_different_model():
    agent = Agent(
        tool_registry=ToolRegistry(),
        model=TestModel(),
    )

    result = agent.run(
        "Hello"
    )

    assert result == "Test model response."


class RecordingModel:
    def __init__(self):
        self.tools = None

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:
        self.tools = request.tools

        return AgentResponse(
            content="Recorded model response."
        )


def test_agent_passes_tool_schemas_to_model():
    model = RecordingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    agent.run("Hello")

    assert model.tools == []


def test_agent_builds_model_request():
    class InspectingModel:
        def __init__(self):
            self.request = None

        def generate(
            self,
            request: ModelRequest,
        ) -> AgentResponse:
            self.request = request

            return AgentResponse(
                content="Hello from inspecting model."
            )

    model = InspectingModel()

    agent = Agent(
        tool_registry=ToolRegistry(),
        model=model,
    )

    result = agent.run("Hello")

    assert result == "Hello from inspecting model."

    assert model.request.messages == [
        {
            "role": "user",
            "content": "Hello",
            "metadata": None,
        }
    ]

    assert model.request.tools == []


def test_agent_state_starts_running_and_completes():
    agent = create_agent()

    result = agent.run("Hello")

    assert (
        result
        == "I don't need a tool to answer that."
    )

    assert agent.state.status == "completed"
    assert agent.state.iteration == 1


def test_agent_state_tracks_multiple_iterations():
    agent = create_agent()

    agent.run(
        "What is my balance?"
    )

    assert agent.state.status == "completed"
    assert agent.state.iteration == 2


def test_agent_state_marks_failure():
    agent = create_agent(
        max_iterations=1
    )

    try:
        agent.run(
            "Check my balance and my invoice."
        )
        assert False
    except RuntimeError:
        pass

    assert agent.state.status == "failed"
    assert agent.state.iteration == 1


def test_agent_graph_simple_answer():
    agent = create_agent()

    agent.run("Hello")

    assert agent.state.node_history == [
        AgentNode.MODEL,
        AgentNode.END,
    ]


def test_agent_graph_single_tool():
    agent = create_agent()

    agent.run(
        "What is my balance?"
    )

    assert agent.state.node_history == [
        AgentNode.MODEL,
        AgentNode.TOOL,
        AgentNode.MODEL,
        AgentNode.END,
    ]


def test_agent_graph_multiple_tools():
    agent = create_agent()

    agent.run(
        "Check my balance and my invoice."
    )

    assert agent.state.node_history == [
        AgentNode.MODEL,
        AgentNode.TOOL,
        AgentNode.MODEL,
        AgentNode.TOOL,
        AgentNode.MODEL,
        AgentNode.END,
    ]


def test_agent_graph_failure():
    agent = create_agent(
        max_iterations=1
    )

    try:
        agent.run(
            "Check my balance and my invoice."
        )
        assert False
    except RuntimeError:
        pass

    assert agent.state.node_history == [
        AgentNode.MODEL,
        AgentNode.TOOL,
        AgentNode.END,
    ]