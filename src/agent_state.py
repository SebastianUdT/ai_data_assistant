from dataclasses import dataclass, field

from src.agent_graph import AgentNode


@dataclass
class AgentState:
    iteration: int = 0
    status: str = "running"
    node: AgentNode = AgentNode.MODEL
    node_history: list[AgentNode] = field(
        default_factory=list
    )

    def move_to(
        self,
        node: AgentNode,
    ) -> None:
        self.node = node
        self.node_history.append(node)

    def reset(self) -> None:
        self.iteration = 0
        self.status = "running"
        self.node = AgentNode.MODEL
        self.node_history = []