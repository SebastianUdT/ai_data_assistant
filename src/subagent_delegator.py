from dataclasses import dataclass

from src.delegation_context import DelegationContext
from src.subagent_selector import SubagentSelector


@dataclass
class DelegationResult:
    subagent_name: str
    task: str
    result: str


class SubagentDelegator:
    def __init__(
        self,
        selector: SubagentSelector,
    ) -> None:
        self.selector = selector

    def delegate(
        self,
        task: str,
        context: DelegationContext | None = None,
    ) -> DelegationResult:
        subagent = self.selector.select(
            task
        )

        if subagent is None:
            raise ValueError(
                "No suitable subagent found."
            )

        delegated_task = task

        if context is not None:
            delegated_task = context.build_task(
                task
            )

        result = subagent.run(
            delegated_task
        )

        return DelegationResult(
            subagent_name=subagent.name,
            task=task,
            result=result,
        )