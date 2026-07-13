"""Customer entity — KYC info, risk profile, account stats."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KYCStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"


class Customer(BaseModel):
    __tablename__ = "customers"

    # Identity
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    country = Column(String(2), nullable=False)  # ISO-3166 alpha-2

    # KYC
    kyc_status = Column(Enum(KYCStatus), default=KYCStatus.PENDING)
    kyc_date = Column(DateTime, nullable=True)

    # Risk profile
    risk_score = Column(Float, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)

    # Account stats
    total_transactions = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    last_transaction_at = Column(DateTime, nullable=True)

    # Flags
    is_active = Column(Boolean, default=True)
    is_sanctioned = Column(Boolean, default=False)
    sanctioned_at = Column(DateTime, nullable=True)

    # Relationships
    transactions = relationship(
        "Transaction", back_populates="customer", cascade="all, delete-orphan"
    )
    alerts = relationship(
        "Alert", back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Customer {self.email} risk={self.risk_level.value}>"