"""
Minimal Production Agent Observability

Extracts safe execution metadata from OpenAI Agents SDK
run results.

Security:
    Do not log customer identifiers, prompts,
    tool arguments, or financial values.

No external services required.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionReport:
    status: str
    tool_names: tuple[str, ...]
    tool_call_count: int
    error_type: str | None = None


def build_execution_report(
    result: Any = None,
    *,
    error: Exception | None = None,
) -> ExecutionReport:
    """
    Build a structured report from an agent execution.

    A result indicates that Runner.run returned successfully.
    An exception indicates that execution failed.
    """

    if error is not None:
        return ExecutionReport(
            status="failed",
            tool_names=(),
            tool_call_count=0,
            error_type=type(error).__name__,
        )

    if result is None:
        raise ValueError("A run result or an error is required.")

    tool_names = []

    for item in result.new_items:
        raw_item = getattr(item, "raw_item", None)

        if getattr(raw_item, "type", None) == "function_call":
            tool_names.append(raw_item.name)

    return ExecutionReport(
        status="completed",
        tool_names=tuple(tool_names),
        tool_call_count=len(tool_names),
    )