from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed: bool
    feedback: str = ""


class Validator(ABC):
    @abstractmethod
    def validate(
        self,
        result: str,
    ) -> ValidationResult:
        pass