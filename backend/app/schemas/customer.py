"""Pydantic schemas for Customer request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    country: str = Field(..., min_length=2, max_length=2)


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    kyc_status: Optional[str] = None


class CustomerResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str]
    country: str
    kyc_status: str
    risk_score: float
    risk_level: str
    total_transactions: int
    total_volume: float
    is_active: bool
    is_sanctioned: bool
    last_transaction_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True