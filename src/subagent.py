from dataclasses import dataclass

from src.agent import Agent


@dataclass
class Subagent:
    name: str
    description: str
    agent: Agent

    def run(
        self,
        task: str,
    ) -> str:
        return self.agent.run(
            task
        )