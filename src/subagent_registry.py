from src.subagent import Subagent


class SubagentRegistry:
    def __init__(
        self,
    ) -> None:
        self._subagents: dict[str, Subagent] = {}

    def register(
        self,
        subagent: Subagent,
    ) -> None:
        self._subagents[subagent.name] = subagent

    def get(
        self,
        name: str,
    ) -> Subagent:
        try:
            return self._subagents[name]
        except KeyError:
            raise ValueError(
                f"Unknown subagent: {name}"
            )

    def list_subagents(
        self,
    ) -> list[Subagent]:
        return list(
            self._subagents.values()
        )

    def descriptions(
        self,
    ) -> list[dict[str, str]]:
        return [
            {
                "name": subagent.name,
                "description": subagent.description,
            }
            for subagent in self._subagents.values()
        ]
    