from src.validator import (
    ValidationResult,
    Validator,
)


class ExpectedTextValidator(Validator):
    def __init__(
        self,
        expected_text: str,
    ) -> None:
        self.expected_text = expected_text

    def validate(
        self,
        result: str,
    ) -> ValidationResult:
        if self.expected_text in result:
            return ValidationResult(
                passed=True,
            )

        return ValidationResult(
            passed=False,
            feedback=(
                "Expected result to contain: "
                f"{self.expected_text}"
            ),
        )