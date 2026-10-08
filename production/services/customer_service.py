"""
Customer Service

PURPOSE
-------
Own deterministic customer business rules.

The service preserves execution metadata and passes trusted actor /
tenant identity to the repository so durable business events are
self-contained.
"""

from dataclasses import dataclass

from production.repositories.customer_repository import (
    CustomerRepository,
)


# =====================================================================
# ERRORS
# =====================================================================


class CustomerNotFoundError(Exception):
    pass


class InvalidCreditAdjustmentError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


# =====================================================================
# RESULT
# =====================================================================


@dataclass(frozen=True)
class CreditAdjustmentOutcome:
    new_balance: float
    replayed: bool


# =====================================================================
# SERVICE
# =====================================================================


class CustomerService:

    def __init__(
        self,
        repository: CustomerRepository | None = None,
    ) -> None:

        self.repository = (
            repository
            or CustomerRepository()
        )

    # =================================================================
    # READ
    # =================================================================

    def get_balance(
        self,
        customer_id: str,
    ) -> float:

        balance = self.repository.get_balance(
            customer_id
        )

        if balance is None:
            raise CustomerNotFoundError(
                f"Customer not found: "
                f"{customer_id}"
            )

        return balance

    # =================================================================
    # WRITE
    # =================================================================

    def apply_credit_adjustment(
        self,
        *,
        operation_id: str,
        user_id: str,
        company_id: str,
        customer_id: str,
        amount: float,
    ) -> CreditAdjustmentOutcome:

        if (
            not operation_id
            or not operation_id.strip()
        ):
            raise ValueError(
                "Operation ID is required."
            )

        if not user_id.strip():
            raise ValueError(
                "User ID is required."
            )

        if not company_id.strip():
            raise ValueError(
                "Company ID is required."
            )

        if amount <= 0:
            raise InvalidCreditAdjustmentError(
                "Credit adjustment must be "
                "greater than zero."
            )

        if amount > 1000:
            raise InvalidCreditAdjustmentError(
                "Credit adjustment cannot "
                "exceed 1000.00."
            )

        try:
            result = (
                self.repository
                .apply_credit_adjustment_idempotent(
                    operation_id=operation_id,
                    user_id=user_id,
                    company_id=company_id,
                    customer_id=customer_id,
                    amount=amount,
                )
            )

        except ValueError as error:
            raise IdempotencyConflictError(
                str(error)
            ) from error

        if result is None:
            raise CustomerNotFoundError(
                f"Customer not found: "
                f"{customer_id}"
            )

        return CreditAdjustmentOutcome(
            new_balance=result.new_balance,
            replayed=(
                result.already_processed
            ),
        )