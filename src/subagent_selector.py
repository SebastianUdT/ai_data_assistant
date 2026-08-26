from src.subagent import Subagent
from src.subagent_registry import SubagentRegistry


class SubagentSelector:
    def __init__(
        self,
        registry: SubagentRegistry,
    ) -> None:
        self.registry = registry

    def select(
        self,
        task: str,
    ) -> Subagent | None:
        task_text = task.lower()

        for subagent in self.registry.list_subagents():
            searchable_text = (
                subagent.name.replace("_", " ")
                + " "
                + subagent.description
            ).lower()

            words = searchable_text.split()

            for word in words:
                if (
                    len(word) >= 4
                    and word in task_text
                ):
                    return subagent

        return None