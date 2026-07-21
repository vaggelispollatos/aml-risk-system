"""Compliance assessment lifecycle: run the Compliance Officer Agent against
an alert, persist the opinion, and let it be queried by the dashboard."""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import AlertNotFoundError
from app.db.models.alert import Alert
from app.db.models.compliance_assessment import ComplianceAssessment
from app.db.models.customer import Customer
from app.services.compliance_officer_agent import ComplianceOfficerAgent

logger = logging.getLogger(__name__)


class ComplianceService:

    def __init__(self, db: Session):
        self.db = db
        self.agent = ComplianceOfficerAgent()

    def assess_alert(self, alert_id: str) -> ComplianceAssessment:
        """Run the agent against an alert and persist the resulting opinion."""
        alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise AlertNotFoundError(alert_id)

        customer = self.db.query(Customer).filter(Customer.id == alert.customer_id).first()

        opinion = self.agent.assess(
            rule_triggered=alert.rule_triggered,
            severity=alert.severity.value,
            reason=alert.reason,
            customer_name=customer.name if customer else "Unknown customer",
            customer_risk_level=customer.risk_level.value if customer else "low",
            customer_kyc_status=customer.kyc_status.value if customer else "pending",
            is_sanctioned=customer.is_sanctioned if customer else False,
        )

        assessment = ComplianceAssessment(
            alert_id=alert.id,
            customer_id=alert.customer_id,
            legal_risk_level=opinion["legal_risk_level"],
            recommended_action=opinion["recommended_action"],
            regulatory_citations=opinion["regulatory_citations"],
            narrative=opinion["narrative"],
            confidence=opinion["confidence"],
            sar_filing_deadline=opinion["sar_filing_deadline"],
            ofac_report_deadline=opinion["ofac_report_deadline"],
            agent_version=opinion["agent_version"],
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        logger.info(
            "Compliance assessment created for alert %s: %s",
            alert_id,
            assessment.recommended_action.value,
        )
        return assessment

    def get_by_id(self, assessment_id: str) -> ComplianceAssessment | None:
        return (
            self.db.query(ComplianceAssessment)
            .filter(ComplianceAssessment.id == assessment_id)
            .first()
        )

    def get_latest_for_alert(self, alert_id: str) -> ComplianceAssessment | None:
        return (
            self.db.query(ComplianceAssessment)
            .filter(ComplianceAssessment.alert_id == alert_id)
            .order_by(ComplianceAssessment.created_at.desc())
            .first()
        )

    def list_assessments(
        self,
        skip: int = 0,
        limit: int = 50,
        recommended_action: str | None = None,
        legal_risk_level: str | None = None,
        customer_id: str | None = None,
    ) -> list[ComplianceAssessment]:
        q = self.db.query(ComplianceAssessment)
        if recommended_action:
            q = q.filter(ComplianceAssessment.recommended_action == recommended_action)
        if legal_risk_level:
            q = q.filter(ComplianceAssessment.legal_risk_level == legal_risk_level)
        if customer_id:
            q = q.filter(ComplianceAssessment.customer_id == customer_id)
        return (
            q.order_by(ComplianceAssessment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
