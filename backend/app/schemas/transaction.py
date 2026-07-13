"""Pydantic schemas for Transaction request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    customer_id: str
    type: str = Field(..., pattern="^(deposit|withdrawal|transfer)$")
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    source_country: Optional[str] = Field(None, min_length=2, max_length=2)
    destination_country: Optional[str] = Field(None, min_length=2, max_length=2)


class TransactionResponse(BaseModel):
    id: str
    customer_id: str
    type: str
    amount: float
    currency: str
    source_country: Optional[str]
    destination_country: Optional[str]
    risk_score: float
    risk_level: Optional[str]
    flagged: bool
    status: str
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True