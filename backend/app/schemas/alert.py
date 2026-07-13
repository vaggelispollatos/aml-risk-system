"""Pydantic schemas for Alert request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: str
    customer_id: str
    transaction_id: Optional[str]
    rule_triggered: str
    severity: str
    reason: str
    status: str
    reviewed: bool
    reviewed_by: Optional[str]
    action_taken: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertReview(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    action_taken: Optional[str] = None
    reviewed_by: Optional[str] = None