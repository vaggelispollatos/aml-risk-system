"""Compliance assessment entity — legal/regulatory opinion produced by the
automated Compliance Officer Agent for a given alert."""

import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, JSON, String, Text

from app.db.base import BaseModel


class RecommendedAction(str, enum.Enum):
    CLOSE_NO_ACTION = "close_no_action"
    ENHANCED_MONITORING = "enhanced_monitoring"
    ENHANCED_DUE_DILIGENCE = "enhanced_due_diligence"
    FILE_SAR = "file_sar"
    BLOCK_AND_FILE_OFAC_REPORT = "block_and_file_ofac_report"


class LegalRiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceAssessment(BaseModel):
    __tablename__ = "compliance_assessments"

    # References
    alert_id = Column(
        String(36),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        String(36),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Opinion
    legal_risk_level = Column(Enum(LegalRiskLevel), nullable=False, index=True)
    recommended_action = Column(Enum(RecommendedAction), nullable=False, index=True)
    regulatory_citations = Column(JSON, nullable=False, default=list)
    narrative = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)

    # Regulatory deadlines (computed when applicable)
    sar_filing_deadline = Column(DateTime, nullable=True)
    ofac_report_deadline = Column(DateTime, nullable=True)

    # Provenance
    agent_version = Column(String(20), default="1.0")

    def __repr__(self) -> str:
        return (
            f"<ComplianceAssessment alert={self.alert_id} "
            f"action={self.recommended_action.value}>"
        )
