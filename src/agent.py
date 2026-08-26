from src.model import Model
from src.agent_context import AgentContext
from src.agent_state import AgentState
from src.agent_graph import (
    AgentNode,
    get_next_node,
)
from src.agent_nodes import (
    run_model_node,
    run_tool_node,
)
from src.context_policy import ContextPolicy
from src.request_builder import build_model_request
from src.tool_registry import ToolRegistry
from src.mcp_client import MCPClient
from src.mcp_types import MCPToolCall
from src.semantic_memory import (
    MemoryEntry,
    SemanticMemory,
)
from src.skill_registry import SkillRegistry
from src.skill_selector import SkillSelector
from src.tools import (
    get_customer_balance,
    get_customer_invoice,
)
from src.fake_model import FakeModel


class Agent:
    def __init__(
        self,
        tool_registry: ToolRegistry,
        model: Model,
        max_iterations: int = 5,
        mcp_client: MCPClient | None = None,
        skill_registry: SkillRegistry | None = None,
        semantic_memory: SemanticMemory | None = None,
        context_policy: ContextPolicy | None = None,
    ):
        self.tool_registry = tool_registry
        self.model = model
        self.max_iterations = max_iterations
        self.mcp_client = mcp_client
        self.skill_registry = skill_registry
        self.semantic_memory = semantic_memory

        self.context_policy = (
            context_policy
            if context_policy is not None
            else ContextPolicy()
        )

        self.skill_selector = (
            SkillSelector(skill_registry)
            if skill_registry is not None
            else None
        )

        self.context = AgentContext()
        self.state = AgentState()

    @property
    def conversation(self):
        return self.context.conversation

    def _is_local_tool(
        self,
        tool_name: str,
    ) -> bool:
        return any(
            tool.name == tool_name
            for tool in self.tool_registry.list_tools()
        )

    def _execute_tool(
        self,
        response,
    ):
        tool_name = response.tool_name

        if tool_name is None:
            raise ValueError(
                "Tool execution requires a tool name."
            )

        if self._is_local_tool(tool_name):
            return run_tool_node(
                tool_registry=self.tool_registry,
                response=response,
            )

        if self.mcp_client is not None:
            mcp_result = self.mcp_client.call_tool(
                MCPToolCall(
                    name=tool_name,
                    arguments=(
                        response.arguments or {}
                    ),
                )
            )

            return mcp_result.result

        return run_tool_node(
            tool_registry=self.tool_registry,
            response=response,
        )

    def _retrieve_memories(
        self,
        user_message: str,
    ) -> list[MemoryEntry]:
        if self.semantic_memory is None:
            return []

        words = user_message.lower().split()

        memories: list[MemoryEntry] = []

        for word in words:
            cleaned_word = (
                word.strip(
                    ".,!?;:'\"()[]{}"
                )
            )

            if len(cleaned_word) < 4:
                continue

            results = self.semantic_memory.search(
                query=cleaned_word
            )

            for memory in results:
                if memory not in memories:
                    memories.append(
                        memory
                    )

        return memories

    def run(
        self,
        user_message: str,
    ) -> str:
        self.context.add_message(
            role="user",
            content=user_message,
        )

        self.state.reset()

        selected_skill = None

        if self.skill_selector is not None:
            selected_skill = (
                self.skill_selector.select(
                    user_message
                )
            )

        relevant_memories = (
            self._retrieve_memories(
                user_message
            )
        )

        for iteration in range(self.max_iterations):
            self.state.iteration = iteration + 1
            self.state.move_to(
                AgentNode.MODEL
            )

            request = build_model_request(
                context=self.context,
                tool_registry=self.tool_registry,
                context_policy=self.context_policy,
                mcp_client=self.mcp_client,
                skill=selected_skill,
                memories=relevant_memories,
            )

            response = run_model_node(
                model=self.model,
                request=request,
            )

            next_node = get_next_node(
                response
            )

            if next_node == AgentNode.END:
                self.state.status = "completed"
                self.state.move_to(
                    AgentNode.END
                )

                answer = response.content or ""

                self.context.add_message(
                    role="assistant",
                    content=answer,
                )

                return answer

            self.state.move_to(
                AgentNode.TOOL
            )

            self.context.add_tool_call(
                tool_name=response.tool_name,
                arguments=response.arguments or {},
            )

            result = self._execute_tool(
                response
            )

            self.context.add_tool_result(
                tool_name=response.tool_name,
                result=result,
            )

        self.state.status = "failed"
        self.state.move_to(
            AgentNode.END
        )

        raise RuntimeError(
            "Agent exceeded the maximum number "
            "of iterations."
        )


def create_agent(
    max_iterations: int = 5,
    model: Model | None = None,
    mcp_client: MCPClient | None = None,
    skill_registry: SkillRegistry | None = None,
    semantic_memory: SemanticMemory | None = None,
    context_policy: ContextPolicy | None = None,
) -> Agent:
    registry = ToolRegistry()

    registry.register(
        name="get_customer_balance",
        description="Get the customer's account balance.",
        function=get_customer_balance,
    )

    registry.register(
        name="get_customer_invoice",
        description="Get the customer's invoice amount.",
        function=get_customer_invoice,
    )

    if model is None:
        model = FakeModel()

    return Agent(
        tool_registry=registry,
        model=model,
        max_iterations=max_iterations,
        mcp_client=mcp_client,
        skill_registry=skill_registry,
        semantic_memory=semantic_memory,
        context_policy=context_policy,
    )