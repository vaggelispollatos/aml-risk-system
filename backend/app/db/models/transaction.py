"""Transaction entity — financial movement records."""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String,
)
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class Transaction(BaseModel):
    __tablename__ = "transactions"

    # Customer link
    customer_id = Column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer = relationship("Customer", back_populates="transactions")

    # Details
    type = Column(Enum(TransactionType), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # Geography
    source_country = Column(String(2), nullable=True)
    destination_country = Column(String(2), nullable=True)

    # Risk assessment
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(20), nullable=True)
    flagged = Column(Boolean, default=False, index=True)

    # Processing
    status = Column(
        Enum(TransactionStatus), default=TransactionStatus.PENDING, index=True
    )
    processed_at = Column(DateTime, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Review
    review_notes = Column(String(500), nullable=True)

    # Extra data
    metadata_ = Column("metadata", JSON, nullable=True)

    # Relationships
    alerts = relationship("Alert", back_populates="transaction")

    def __repr__(self) -> str:
        return f"<Transaction {self.id[:8]} ${self.amount} {self.status.value}>"