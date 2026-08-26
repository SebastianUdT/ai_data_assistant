from typing import Any

from src.agent_model import AgentResponse
from src.model import Model
from src.model_request import ModelRequest


class FakeModel(Model):

    def _find_tool(
        self,
        tools: list[dict[str, Any]],
        keyword: str,
    ) -> dict[str, Any] | None:

        for tool in tools:
            text = (
                tool["name"]
                + " "
                + tool["description"]
            ).lower()

            if keyword in text:
                return tool

        return None

    def _build_arguments(
        self,
        tool: dict[str, Any],
    ) -> dict[str, Any]:

        parameters = tool["parameters"]

        arguments: dict[str, Any] = {}

        for name in parameters:
            if name == "customer_id":
                arguments[name] = "customer_001"

        return arguments

    def _get_tool_results(
        self,
        request: ModelRequest,
    ) -> list[dict[str, Any]]:

        results = []

        for message in request.messages:
            if message.get("role") == "tool_result":
                metadata = message.get("metadata")

                if metadata and "result" in metadata:
                    results.append(
                        metadata["result"]
                    )

        return results

    def generate(
        self,
        request: ModelRequest,
    ) -> AgentResponse:

        context = " ".join(
            str(message.get("content", ""))
            for message in request.messages
        ).lower()

        tools = request.tools
        results = self._get_tool_results(request)

        for result in results:
            if "error" in result:
                return AgentResponse(
                    content=(
                        "I couldn't complete the request "
                        "because the tool returned an error: "
                        f"{result['error']}"
                    )
                )

        balance = None
        invoice = None

        for result in results:
            if "balance" in result:
                balance = result["balance"]

            if "amount" in result:
                invoice = result["amount"]

        if (
            "balance" in context
            and balance is None
        ):
            tool = self._find_tool(
                tools,
                "balance",
            )

            if tool is not None:
                return AgentResponse(
                    tool_name=tool["name"],
                    arguments=self._build_arguments(
                        tool
                    ),
                )

        if (
            "invoice" in context
            and invoice is None
        ):
            tool = self._find_tool(
                tools,
                "invoice",
            )

            if tool is not None:
                return AgentResponse(
                    tool_name=tool["name"],
                    arguments=self._build_arguments(
                        tool
                    ),
                )

        if (
            balance is not None
            and invoice is not None
        ):
            return AgentResponse(
                content=(
                    f"Your balance is "
                    f"${balance:.2f} "
                    f"and your invoice is "
                    f"${invoice:.2f}."
                )
            )

        if balance is not None:
            return AgentResponse(
                content=(
                    f"Your balance is "
                    f"${balance:.2f}."
                )
            )

        if invoice is not None:
            return AgentResponse(
                content=(
                    f"Your invoice is "
                    f"${invoice:.2f}."
                )
            )

        return AgentResponse(
            content="I don't need a tool to answer that."
        )