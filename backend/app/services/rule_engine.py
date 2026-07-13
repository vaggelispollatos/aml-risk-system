"""
AML Rule Engine — evaluates transactions against configurable risk rules.

Each Rule subclass implements .evaluate() returning (result, score, reason).
The RuleEngine runs all rules and produces a combined risk assessment.
"""

import logging
from datetime import timedelta
from enum import Enum
from typing import Dict, List, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class RuleResult(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Rule:
    """Base class — every rule must implement evaluate()."""

    def __init__(self, name: str, description: str, severity: str, weight: float = 1.0):
        self.name = name
        self.description = description
        self.severity = severity
        self.weight = weight

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

class TransactionAmountRule(Rule):
    """Flag transactions that exceed a fixed threshold or deviate from the
    customer's historical average."""

    def __init__(self, threshold: float = settings.HIGH_AMOUNT_THRESHOLD):
        super().__init__(
            name="high_transaction_amount",
            description="Transaction exceeds amount threshold",
            severity="high",
            weight=0.25,
        )
        self.threshold = threshold

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        amount = ctx.get("amount", 0)
        avg = ctx.get("customer_avg_transaction", 0)

        if amount > self.threshold:
            score = min(100, (amount / self.threshold) * 50)
            return (
                RuleResult.FAILED,
                score,
                f"Amount ${amount:,.2f} exceeds threshold ${self.threshold:,.2f}",
            )

        if avg > 0 and amount > avg * 3:
            return (
                RuleResult.WARNING,
                30.0,
                f"Amount ${amount:,.2f} is >3x customer average ${avg:,.2f}",
            )

        return RuleResult.PASSED, 0.0, "Amount within normal range"


class VelocityCheckRule(Rule):
    """Flag bursts of transactions within a short window."""

    def __init__(
        self,
        max_transactions: int = settings.VELOCITY_MAX_TRANSACTIONS,
        window_minutes: int = settings.VELOCITY_WINDOW_MINUTES,
    ):
        super().__init__(
            name="velocity_check",
            description="Too many transactions in short timeframe",
            severity="critical",
            weight=0.30,
        )
        self.max_transactions = max_transactions
        self.window_minutes = window_minutes

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        count = ctx.get("recent_transactions_count", 0)

        if count > self.max_transactions:
            excess = count - self.max_transactions
            score = min(100, 30 + excess * 15)
            return (
                RuleResult.FAILED,
                score,
                f"{count} transactions in {self.window_minutes}min (limit {self.max_transactions})",
            )

        if count >= int(self.max_transactions * 0.8):
            return RuleResult.WARNING, 20.0, f"Approaching velocity limit ({count})"

        return RuleResult.PASSED, 0.0, "Velocity normal"


class GeographicAnomalyRule(Rule):
    """Flag physically impossible travel between consecutive transactions."""

    MAX_SPEED_KMH = 900  # commercial flight

    def __init__(self):
        super().__init__(
            name="geographic_anomaly",
            description="Impossible geographic movement detected",
            severity="high",
            weight=0.20,
        )

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        src = ctx.get("source_country")
        last = ctx.get("customer_last_country")

        if not src or not last or src == last:
            return RuleResult.PASSED, 0.0, "No geographic anomaly"

        distance = ctx.get("distance_km", 0)
        elapsed: timedelta = ctx.get(
            "time_since_last_transaction", timedelta(hours=24)
        )
        elapsed_hours = elapsed.total_seconds() / 3600
        required_hours = distance / self.MAX_SPEED_KMH if distance else 0

        if distance > 1000 and elapsed_hours < required_hours:
            return (
                RuleResult.FAILED,
                75.0,
                f"Impossible travel: {distance}km in {elapsed_hours:.1f}h "
                f"(need {required_hours:.1f}h)",
            )

        return RuleResult.PASSED, 0.0, "Travel plausible"


class SanctionsCheckRule(Rule):
    """Block sanctioned individuals immediately."""

    def __init__(self):
        super().__init__(
            name="sanctions_check",
            description="Customer appears on a sanctions list",
            severity="critical",
            weight=0.25,
        )

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        if ctx.get("is_sanctioned", False):
            return RuleResult.FAILED, 100.0, "Customer matches sanctions list"
        return RuleResult.PASSED, 0.0, "Not on sanctions list"


class KYCStatusRule(Rule):
    """Penalise transactions from customers whose KYC is incomplete."""

    def __init__(self):
        super().__init__(
            name="kyc_verification",
            description="Customer KYC status check",
            severity="medium",
            weight=0.10,
        )

    def evaluate(self, ctx: Dict) -> Tuple[RuleResult, float, str]:
        status = ctx.get("kyc_status", "pending")
        if status == "approved":
            return RuleResult.PASSED, 0.0, "KYC verified"
        score = 40.0 if status == "pending" else 80.0
        return RuleResult.WARNING, score, f"KYC status is '{status}'"


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """Orchestrates all rules against a transaction context dict."""

    def __init__(self, rules: List[Rule] | None = None):
        self.rules: List[Rule] = rules or [
            TransactionAmountRule(),
            VelocityCheckRule(),
            GeographicAnomalyRule(),
            SanctionsCheckRule(),
            KYCStatusRule(),
        ]

    def evaluate(self, ctx: Dict) -> Dict:
        """Run every rule and return an aggregate risk assessment."""

        triggered: List[Dict] = []
        weighted_total = 0.0
        weight_sum = 0.0

        for rule in self.rules:
            try:
                result, score, reason = rule.evaluate(ctx)
            except Exception:
                logger.exception("Rule %s raised an error", rule.name)
                continue

            weight_sum += rule.weight

            if result != RuleResult.PASSED:
                triggered.append(
                    {
                        "rule": rule.name,
                        "severity": rule.severity,
                        "result": result.value,
                        "score": score,
                        "reason": reason,
                    }
                )
                weighted_total += score * rule.weight

        final_score = round(
            min(100, max(0, weighted_total / weight_sum)) if weight_sum else 0,
            2,
        )
        level = self._level(final_score)
        has_critical = any(
            r["severity"] == "critical" and r["result"] == "failed"
            for r in triggered
        )

        return {
            "risk_score": final_score,
            "risk_level": level,
            "triggered_rules": triggered,
            "should_flag": level in ("high", "critical"),
            "should_block": level == "critical" or has_critical,
        }

    @staticmethod
    def _level(score: float) -> str:
        if score < 25:
            return "low"
        if score < 50:
            return "medium"
        if score < 75:
            return "high"
        return "critical"