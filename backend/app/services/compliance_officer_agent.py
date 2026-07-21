"""Compliance Officer Agent — an automated legal/regulatory reviewer.

Given a triggered AML alert plus the underlying customer (and, where
available, transaction) context, the agent produces a structured
compliance opinion: applicable regulatory citations, a recommended
action, filing deadlines where relevant, and a narrative memorandum
suitable for a human BSA/AML or legal officer to review.

This is a rules-based legal-knowledge engine (no external LLM calls),
mirroring the deterministic style of ``rule_engine.py`` so opinions are
explainable, reproducible, and auditable — a hard requirement for any
system that feeds real compliance decisions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.db.models.compliance_assessment import LegalRiskLevel, RecommendedAction

AGENT_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Regulatory knowledge base
# ---------------------------------------------------------------------------
# Citations that apply to every assessment, regardless of which rule fired.
BASE_CITATIONS: List[Dict[str, str]] = [
    {
        "statute": "31 U.S.C. § 5318(g) / 31 CFR § 1020.320",
        "requirement": "Bank Secrecy Act — Suspicious Activity Report (SAR) filing obligation",
    },
]

# Citations keyed by the AML rule that produced the alert (rule_engine.py names).
RULE_CITATIONS: Dict[str, List[Dict[str, str]]] = {
    "high_transaction_amount": [
        {
            "statute": "31 CFR § 1010.311",
            "requirement": "Currency Transaction Report (CTR) — required for currency transactions over $10,000",
        },
    ],
    "velocity_check": [
        {
            "statute": "31 U.S.C. § 5324",
            "requirement": "Anti-structuring statute — prohibits breaking transactions into "
            "smaller amounts to evade reporting thresholds",
        },
    ],
    "geographic_anomaly": [
        {
            "statute": "FATF Recommendation 10 / FinCEN Geographic Targeting Orders",
            "requirement": "Heightened scrutiny of transactions involving higher-risk jurisdictions "
            "or implausible geographic patterns",
        },
    ],
    "sanctions_check": [
        {
            "statute": "Executive Order 13224 / 31 CFR Chapter V",
            "requirement": "OFAC sanctions regulations — assets of designated persons must be blocked",
        },
        {
            "statute": "31 CFR § 501.603",
            "requirement": "Blocked property must be reported to OFAC within 10 business days",
        },
    ],
    "kyc_verification": [
        {
            "statute": "31 CFR § 1020.220",
            "requirement": "Customer Identification Program (CIP) requirements",
        },
        {
            "statute": "31 CFR § 1010.230",
            "requirement": "Customer Due Diligence (CDD) Final Rule — beneficial ownership verification",
        },
    ],
}

SAR_FILING_WINDOW_DAYS = 30
OFAC_REPORT_WINDOW_BUSINESS_DAYS = 10

_ACTION_LABELS = {
    RecommendedAction.CLOSE_NO_ACTION: "Close — no further action required",
    RecommendedAction.ENHANCED_MONITORING: "Continue enhanced monitoring",
    RecommendedAction.ENHANCED_DUE_DILIGENCE: "Perform Enhanced Due Diligence (EDD)",
    RecommendedAction.FILE_SAR: "File a Suspicious Activity Report (SAR)",
    RecommendedAction.BLOCK_AND_FILE_OFAC_REPORT: "Block assets and file an OFAC blocked-property report",
}


def _add_business_days(start: datetime, business_days: int) -> datetime:
    """Advance ``start`` by ``business_days``, skipping weekends."""
    current = start
    remaining = business_days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            remaining -= 1
    return current


class ComplianceOfficerAgent:
    """Deterministic legal/compliance opinion engine."""

    def assess(
        self,
        *,
        rule_triggered: str,
        severity: str,
        reason: str,
        customer_name: str,
        customer_risk_level: str,
        customer_kyc_status: str,
        is_sanctioned: bool,
        now: Optional[datetime] = None,
    ) -> Dict:
        """Produce a compliance opinion for a single triggered alert."""
        now = now or datetime.utcnow()

        legal_risk_level = self._legal_risk_level(severity, customer_risk_level, is_sanctioned)
        recommended_action = self._recommended_action(
            rule_triggered, severity, customer_kyc_status, is_sanctioned
        )
        citations = self._citations(rule_triggered)
        confidence = self._confidence(legal_risk_level, is_sanctioned, customer_kyc_status)

        sar_deadline = None
        ofac_deadline = None
        if recommended_action in (RecommendedAction.FILE_SAR, RecommendedAction.BLOCK_AND_FILE_OFAC_REPORT):
            sar_deadline = now + timedelta(days=SAR_FILING_WINDOW_DAYS)
        if recommended_action == RecommendedAction.BLOCK_AND_FILE_OFAC_REPORT:
            ofac_deadline = _add_business_days(now, OFAC_REPORT_WINDOW_BUSINESS_DAYS)

        narrative = self._narrative(
            customer_name=customer_name,
            rule_triggered=rule_triggered,
            severity=severity,
            reason=reason,
            legal_risk_level=legal_risk_level,
            recommended_action=recommended_action,
            citations=citations,
            sar_deadline=sar_deadline,
            ofac_deadline=ofac_deadline,
            is_sanctioned=is_sanctioned,
        )

        return {
            "legal_risk_level": legal_risk_level,
            "recommended_action": recommended_action,
            "regulatory_citations": citations,
            "narrative": narrative,
            "confidence": confidence,
            "sar_filing_deadline": sar_deadline,
            "ofac_report_deadline": ofac_deadline,
            "agent_version": AGENT_VERSION,
        }

    # -- decision logic ----------------------------------------------------

    @staticmethod
    def _legal_risk_level(severity: str, customer_risk_level: str, is_sanctioned: bool) -> LegalRiskLevel:
        if is_sanctioned or severity == "critical":
            return LegalRiskLevel.CRITICAL
        if severity == "high" or customer_risk_level == "critical":
            return LegalRiskLevel.HIGH
        if severity == "medium" or customer_risk_level == "high":
            return LegalRiskLevel.MEDIUM
        return LegalRiskLevel.LOW

    @staticmethod
    def _recommended_action(
        rule_triggered: str, severity: str, customer_kyc_status: str, is_sanctioned: bool
    ) -> RecommendedAction:
        if is_sanctioned or rule_triggered == "sanctions_check":
            return RecommendedAction.BLOCK_AND_FILE_OFAC_REPORT
        if severity == "critical":
            return RecommendedAction.FILE_SAR
        if severity == "high" or customer_kyc_status in ("pending", "rejected", "suspended"):
            return RecommendedAction.ENHANCED_DUE_DILIGENCE
        if severity == "medium":
            return RecommendedAction.ENHANCED_MONITORING
        return RecommendedAction.CLOSE_NO_ACTION

    @staticmethod
    def _citations(rule_triggered: str) -> List[Dict[str, str]]:
        citations = list(BASE_CITATIONS) + list(RULE_CITATIONS.get(rule_triggered, []))
        # De-duplicate while preserving order.
        seen = set()
        unique: List[Dict[str, str]] = []
        for c in citations:
            key = c["statute"]
            if key not in seen:
                seen.add(key)
                unique.append(c)
        return unique

    @staticmethod
    def _confidence(legal_risk_level: LegalRiskLevel, is_sanctioned: bool, customer_kyc_status: str) -> float:
        base = {
            LegalRiskLevel.LOW: 0.6,
            LegalRiskLevel.MEDIUM: 0.7,
            LegalRiskLevel.HIGH: 0.8,
            LegalRiskLevel.CRITICAL: 0.9,
        }[legal_risk_level]
        if is_sanctioned:
            base = max(base, 0.95)
        if customer_kyc_status != "approved":
            base = min(1.0, base + 0.05)
        return round(base, 2)

    # -- narrative -----------------------------------------------------------

    @staticmethod
    def _narrative(
        *,
        customer_name: str,
        rule_triggered: str,
        severity: str,
        reason: str,
        legal_risk_level: LegalRiskLevel,
        recommended_action: RecommendedAction,
        citations: List[Dict[str, str]],
        sar_deadline: Optional[datetime],
        ofac_deadline: Optional[datetime],
        is_sanctioned: bool,
    ) -> str:
        citation_lines = "\n".join(
            f"  - {c['statute']}: {c['requirement']}" for c in citations
        )

        lines = [
            "COMPLIANCE ASSESSMENT MEMORANDUM",
            "",
            f"Customer: {customer_name}",
            f"Alert rule: {rule_triggered} ({severity.upper()} severity)",
            f"Basis: {reason}",
            "",
            f"Legal risk level: {legal_risk_level.value.upper()}",
            f"Recommended action: {_ACTION_LABELS[recommended_action]}",
            "",
            "Regulatory basis:",
            citation_lines,
        ]

        if is_sanctioned:
            lines += [
                "",
                "This customer matches a sanctions list entry. Applicable funds/assets "
                "must be blocked immediately and frozen pending OFAC guidance; the "
                "customer must not be notified in a manner that would constitute tipping-off.",
            ]

        if ofac_deadline:
            lines += [
                "",
                f"OFAC blocked-property report due by: {ofac_deadline.date().isoformat()} "
                f"({OFAC_REPORT_WINDOW_BUSINESS_DAYS} business days).",
            ]

        if sar_deadline:
            lines += [
                "",
                f"SAR filing due by: {sar_deadline.date().isoformat()} "
                f"({SAR_FILING_WINDOW_DAYS} calendar days from detection). "
                "This deadline may be extended by an additional 30 days if no suspect "
                "has been identified.",
            ]

        lines += [
            "",
            "This assessment is generated by an automated Compliance Officer Agent "
            "based on configured regulatory rules. It does not constitute legal advice "
            "and does not substitute for review and sign-off by a qualified BSA/AML "
            "Officer or legal counsel before any regulatory filing is made.",
        ]

        return "\n".join(lines)
