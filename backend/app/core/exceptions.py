"""Application-specific exceptions."""

from fastapi import HTTPException, status


class CustomerNotFoundError(HTTPException):
    def __init__(self, customer_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )


class TransactionNotFoundError(HTTPException):
    def __init__(self, transaction_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found",
        )


class AlertNotFoundError(HTTPException):
    def __init__(self, alert_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )


class DuplicateEmailError(HTTPException):
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email {email} already exists",
        )


class ComplianceAssessmentNotFoundError(HTTPException):
    def __init__(self, assessment_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compliance assessment {assessment_id} not found",
        )


class TransactionBlockedError(HTTPException):
    def __init__(self, reason: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Transaction blocked: {reason}",
        )