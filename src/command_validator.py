import subprocess
import sys

from src.validator import (
    ValidationResult,
    Validator,
)


class CommandValidator(Validator):
    def __init__(
        self,
        command: list[str],
    ) -> None:
        self.command = command

    @classmethod
    def python_module(
        cls,
        module: str,
        *args: str,
    ) -> "CommandValidator":
        return cls(
            command=[
                sys.executable,
                "-m",
                module,
                *args,
            ]
        )

    def validate(
        self,
        result: str,
    ) -> ValidationResult:
        completed = subprocess.run(
            self.command,
            capture_output=True,
            text=True,
        )

        if completed.returncode == 0:
            return ValidationResult(
                passed=True,
            )

        output_parts = []

        if completed.stdout:
            output_parts.append(
                completed.stdout.strip()
            )

        if completed.stderr:
            output_parts.append(
                completed.stderr.strip()
            )

        output = "\n".join(
            output_parts
        )

        return ValidationResult(
            passed=False,
            feedback=(
                "Validation command failed.\n"
                f"Command: {' '.join(self.command)}"
                + (
                    f"\n\n{output}"
                    if output
                    else ""
                )
            ),
        )