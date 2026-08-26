from subprocess import CompletedProcess
from unittest.mock import patch

from src.command_validator import CommandValidator


def test_command_validator_passes_on_zero_exit_code():
    validator = CommandValidator(
        command=[
            "python",
            "-m",
            "pytest",
        ]
    )

    completed = CompletedProcess(
        args=[
            "python",
            "-m",
            "pytest",
        ],
        returncode=0,
        stdout="117 passed",
        stderr="",
    )

    with patch(
        "src.command_validator.subprocess.run",
        return_value=completed,
    ) as mocked_run:
        validation = validator.validate(
            "Agent result."
        )

    assert validation.passed is True
    assert validation.feedback == ""

    mocked_run.assert_called_once_with(
        [
            "python",
            "-m",
            "pytest",
        ],
        capture_output=True,
        text=True,
    )


def test_command_validator_returns_stdout_on_failure():
    validator = CommandValidator(
        command=[
            "python",
            "-m",
            "pytest",
        ]
    )

    completed = CompletedProcess(
        args=[
            "python",
            "-m",
            "pytest",
        ],
        returncode=1,
        stdout=(
            "FAILED test_example.py::"
            "test_example"
        ),
        stderr="",
    )

    with patch(
        "src.command_validator.subprocess.run",
        return_value=completed,
    ):
        validation = validator.validate(
            "Agent result."
        )

    assert validation.passed is False

    assert (
        "Validation command failed."
        in validation.feedback
    )

    assert (
        "Command: python -m pytest"
        in validation.feedback
    )

    assert (
        "FAILED test_example.py::test_example"
        in validation.feedback
    )


def test_command_validator_returns_stderr_on_failure():
    validator = CommandValidator(
        command=["example"]
    )

    completed = CompletedProcess(
        args=["example"],
        returncode=1,
        stdout="",
        stderr="Something went wrong.",
    )

    with patch(
        "src.command_validator.subprocess.run",
        return_value=completed,
    ):
        validation = validator.validate(
            "Agent result."
        )

    assert validation.passed is False

    assert (
        "Something went wrong."
        in validation.feedback
    )


def test_command_validator_combines_output():
    validator = CommandValidator(
        command=["example"]
    )

    completed = CompletedProcess(
        args=["example"],
        returncode=1,
        stdout="Standard output.",
        stderr="Standard error.",
    )

    with patch(
        "src.command_validator.subprocess.run",
        return_value=completed,
    ):
        validation = validator.validate(
            "Agent result."
        )

    assert (
        "Standard output."
        in validation.feedback
    )

    assert (
        "Standard error."
        in validation.feedback
    )