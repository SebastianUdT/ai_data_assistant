from dataclasses import dataclass

from src.agent import Agent
from src.validator import Validator


@dataclass
class HarnessConfig:
    max_iterations: int = 5
    context_message_limit: int = 10
    allow_tools: bool = True
    allow_mcp: bool = True
    allow_subagents: bool = True
    max_validation_attempts: int = 3


class AgentHarness:
    def __init__(
        self,
        config: HarnessConfig | None = None,
    ) -> None:
        self.config = (
            config
            if config is not None
            else HarnessConfig()
        )

    def run(
        self,
        agent: Agent,
        task: str,
        validator: Validator | None = None,
    ) -> str:
        if validator is None:
            return agent.run(
                task
            )

        current_task = task

        for attempt in range(
            self.config.max_validation_attempts
        ):
            result = agent.run(
                current_task
            )

            validation = validator.validate(
                result
            )

            if validation.passed:
                return result

            current_task = (
                f"{task}\n\n"
                "VALIDATION FEEDBACK:\n"
                f"{validation.feedback}\n\n"
                "Try again and correct the problem."
            )

        raise RuntimeError(
            "Harness validation failed after "
            f"{self.config.max_validation_attempts} "
            "attempts."
        )