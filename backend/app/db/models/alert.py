"""Alert entity — suspicious-activity alerts raised by the rule engine."""

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    ESCALATED = "escalated"


class Alert(BaseModel):
    __tablename__ = "alerts"

    # References
    customer_id = Column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer = relationship("Customer", back_populates="alerts")

    transaction_id = Column(
        String(36),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
    )
    transaction = relationship("Transaction", back_populates="alerts")

    # Alert info
    rule_triggered = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    reason = Column(Text, nullable=False)

    # Workflow
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN, index=True)
    reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)
    action_taken = Column(String(200), nullable=True)

    def __repr__(self) -> str:
        return f"<Alert {self.rule_triggered} {self.severity.value} {self.status.value}>"