"""Unit tests for the Compliance Officer Agent's legal/regulatory logic."""

from datetime import datetime

from app.db.models.compliance_assessment import LegalRiskLevel, RecommendedAction
from app.services.compliance_officer_agent import ComplianceOfficerAgent


class TestSanctionsCase:

    def test_sanctioned_customer_blocks_and_files_ofac_report(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="sanctions_check",
            severity="critical",
            reason="Customer matches sanctions list",
            customer_name="Jane Risky",
            customer_risk_level="critical",
            customer_kyc_status="approved",
            is_sanctioned=True,
        )

        assert result["recommended_action"] == RecommendedAction.BLOCK_AND_FILE_OFAC_REPORT
        assert result["legal_risk_level"] == LegalRiskLevel.CRITICAL
        assert result["ofac_report_deadline"] is not None
        assert result["sar_filing_deadline"] is not None
        assert result["confidence"] >= 0.9
        assert any("501.603" in c["statute"] for c in result["regulatory_citations"])
        assert "blocked" in result["narrative"].lower()

    def test_ofac_deadline_is_business_days_only(self):
        agent = ComplianceOfficerAgent()
        # Detected on a Friday — 10 business days must skip both weekends.
        friday = datetime(2026, 7, 24, 12, 0, 0)
        result = agent.assess(
            rule_triggered="sanctions_check",
            severity="critical",
            reason="Sanctions match",
            customer_name="Test",
            customer_risk_level="critical",
            customer_kyc_status="approved",
            is_sanctioned=True,
            now=friday,
        )
        deadline = result["ofac_report_deadline"]
        assert deadline.weekday() < 5
        assert (deadline - friday).days >= 12  # 10 business days spans 2 weekends


class TestSeverityLadder:

    def test_critical_severity_recommends_sar(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="velocity_check",
            severity="critical",
            reason="10 transactions in 60min",
            customer_name="Bob",
            customer_risk_level="high",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        assert result["recommended_action"] == RecommendedAction.FILE_SAR
        assert result["sar_filing_deadline"] is not None
        assert result["ofac_report_deadline"] is None

    def test_high_severity_recommends_edd(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="high_transaction_amount",
            severity="high",
            reason="Amount exceeds threshold",
            customer_name="Bob",
            customer_risk_level="medium",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        assert result["recommended_action"] == RecommendedAction.ENHANCED_DUE_DILIGENCE
        assert result["legal_risk_level"] == LegalRiskLevel.HIGH

    def test_pending_kyc_escalates_to_edd_even_at_medium_severity(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="kyc_verification",
            severity="medium",
            reason="KYC status is 'pending'",
            customer_name="Bob",
            customer_risk_level="low",
            customer_kyc_status="pending",
            is_sanctioned=False,
        )
        assert result["recommended_action"] == RecommendedAction.ENHANCED_DUE_DILIGENCE

    def test_medium_severity_with_approved_kyc_recommends_monitoring(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="high_transaction_amount",
            severity="medium",
            reason=">3x customer average",
            customer_name="Bob",
            customer_risk_level="low",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        assert result["recommended_action"] == RecommendedAction.ENHANCED_MONITORING

    def test_low_severity_closes_with_no_action(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="high_transaction_amount",
            severity="low",
            reason="minor deviation",
            customer_name="Bob",
            customer_risk_level="low",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        assert result["recommended_action"] == RecommendedAction.CLOSE_NO_ACTION
        assert result["legal_risk_level"] == LegalRiskLevel.LOW
        assert result["sar_filing_deadline"] is None
        assert result["ofac_report_deadline"] is None


class TestCitationsAndNarrative:

    def test_every_assessment_includes_base_bsa_citation(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="geographic_anomaly",
            severity="high",
            reason="Impossible travel",
            customer_name="Bob",
            customer_risk_level="medium",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        statutes = [c["statute"] for c in result["regulatory_citations"]]
        assert any("5318" in s for s in statutes)

    def test_citations_are_deduplicated(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="unknown_rule_not_in_kb",
            severity="low",
            reason="n/a",
            customer_name="Bob",
            customer_risk_level="low",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        statutes = [c["statute"] for c in result["regulatory_citations"]]
        assert len(statutes) == len(set(statutes))

    def test_narrative_contains_disclaimer(self):
        agent = ComplianceOfficerAgent()
        result = agent.assess(
            rule_triggered="high_transaction_amount",
            severity="high",
            reason="over threshold",
            customer_name="Bob",
            customer_risk_level="medium",
            customer_kyc_status="approved",
            is_sanctioned=False,
        )
        assert "does not constitute legal advice" in result["narrative"]
        assert "Bob" in result["narrative"]
