"""Pydantic schemas for Compliance Officer Agent request/response validation."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RegulatoryCitation(BaseModel):
    statute: str
    requirement: str


class ComplianceAssessmentResponse(BaseModel):
    id: str
    alert_id: str
    customer_id: str
    legal_risk_level: str
    recommended_action: str
    regulatory_citations: list[RegulatoryCitation]
    narrative: str
    confidence: float
    sar_filing_deadline: Optional[datetime]
    ofac_report_deadline: Optional[datetime]
    agent_version: str
    created_at: datetime

    class Config:
        from_attributes = True
