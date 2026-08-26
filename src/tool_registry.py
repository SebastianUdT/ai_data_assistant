from collections.abc import Callable
from dataclasses import dataclass
import inspect
from typing import Any


@dataclass
class Tool:
    name: str
    description: str
    function: Callable[..., Any]

    def schema(self) -> dict[str, Any]:
        signature = inspect.signature(
            self.function
        )

        parameters: dict[str, Any] = {}

        for name, parameter in signature.parameters.items():
            parameters[name] = {
                "type": self._get_type_name(
                    parameter.annotation
                ),
                "required": (
                    parameter.default
                    is inspect.Parameter.empty
                ),
            }

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
        }

    @staticmethod
    def _get_type_name(
        annotation: Any,
    ) -> str:
        if annotation is inspect.Parameter.empty:
            return "unknown"

        if annotation is str:
            return "string"

        if annotation is int:
            return "integer"

        if annotation is float:
            return "number"

        if annotation is bool:
            return "boolean"

        return str(annotation)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        function: Callable[..., Any],
    ) -> None:
        self._tools[name] = Tool(
            name=name,
            description=description,
            function=function,
        )

    def get(
        self,
        name: str,
    ) -> Tool:
        try:
            return self._tools[name]
        except KeyError:
            raise ValueError(
                f"Unknown tool: {name}"
            )

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def schemas(self) -> list[dict[str, Any]]:
        return [
            tool.schema()
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        tool = self.get(name)

        try:
            return tool.function(
                **arguments
            )
        except Exception as error:
            return {
                "error": str(error),
                "tool": name,
            }