"""Unit tests for every rule and the engine orchestrator."""

from datetime import timedelta

import pytest

from app.services.rule_engine import (
    GeographicAnomalyRule,
    KYCStatusRule,
    RuleEngine,
    RuleResult,
    SanctionsCheckRule,
    TransactionAmountRule,
    VelocityCheckRule,
)


class TestTransactionAmountRule:

    @pytest.fixture()
    def rule(self):
        return TransactionAmountRule(threshold=10_000)

    def test_over_threshold_fails(self, rule):
        r, score, _ = rule.evaluate({"amount": 15_000, "customer_avg_transaction": 0})
        assert r == RuleResult.FAILED
        assert score > 0

    def test_under_threshold_passes(self, rule):
        r, score, _ = rule.evaluate({"amount": 5_000, "customer_avg_transaction": 5_000})
        assert r == RuleResult.PASSED
        assert score == 0

    def test_3x_average_warns(self, rule):
        r, score, _ = rule.evaluate({"amount": 7_000, "customer_avg_transaction": 2_000})
        assert r == RuleResult.WARNING
        assert score == 30

    def test_zero_avg_no_warning(self, rule):
        r, _, _ = rule.evaluate({"amount": 5_000, "customer_avg_transaction": 0})
        assert r == RuleResult.PASSED

    def test_exactly_threshold_passes(self, rule):
        r, _, _ = rule.evaluate({"amount": 10_000, "customer_avg_transaction": 5_000})
        assert r == RuleResult.PASSED

    def test_score_capped_at_100(self, rule):
        _, score, _ = rule.evaluate({"amount": 500_000, "customer_avg_transaction": 0})
        assert score <= 100

class TestVelocityCheckRule:

    @pytest.fixture()
    def rule(self):
        return VelocityCheckRule(max_transactions=5, window_minutes=60)

    def test_over_limit_fails(self, rule):
        r, score, _ = rule.evaluate({"recent_transactions_count": 8})
        assert r == RuleResult.FAILED
        assert score > 0

    def test_under_limit_passes(self, rule):
        r, score, _ = rule.evaluate({"recent_transactions_count": 2})
        assert r == RuleResult.PASSED
        assert score == 0

    def test_at_limit_warns(self, rule):
       r, _, _ = rule.evaluate({"recent_transactions_count": 5})
       assert r == RuleResult.WARNING

    def test_near_limit_warns(self, rule):
        r, score, _ = rule.evaluate({"recent_transactions_count": 4})
        assert r == RuleResult.WARNING
        assert score == 20

    def test_score_scales_with_excess(self, rule):
        _, score_small, _ = rule.evaluate({"recent_transactions_count": 6})
        _, score_big, _ = rule.evaluate({"recent_transactions_count": 10})
        assert score_big > score_small


class TestGeographicAnomalyRule:

    @pytest.fixture()
    def rule(self):
        return GeographicAnomalyRule()

    def test_same_country_passes(self, rule):
        r, _, _ = rule.evaluate({
            "source_country": "US",
            "customer_last_country": "US",
        })
        assert r == RuleResult.PASSED

    def test_impossible_travel_fails(self, rule):
        r, score, reason = rule.evaluate({
            "source_country": "US",
            "customer_last_country": "CN",
            "distance_km": 12_000,
            "time_since_last_transaction": timedelta(minutes=30),
        })
        assert r == RuleResult.FAILED
        assert score == 75
        assert "Impossible" in reason

    def test_plausible_travel_passes(self, rule):
        r, _, _ = rule.evaluate({
            "source_country": "US",
            "customer_last_country": "GB",
            "distance_km": 5_000,
            "time_since_last_transaction": timedelta(hours=24),
        })
        assert r == RuleResult.PASSED

    def test_missing_country_passes(self, rule):
        r, _, _ = rule.evaluate({
            "source_country": "US",
            "customer_last_country": None,
        })
        assert r == RuleResult.PASSED

    def test_short_distance_passes_even_if_fast(self, rule):
        r, _, _ = rule.evaluate({
            "source_country": "US",
            "customer_last_country": "CA",
            "distance_km": 500,
            "time_since_last_transaction": timedelta(minutes=10),
        })
        assert r == RuleResult.PASSED


class TestSanctionsCheckRule:

    @pytest.fixture()
    def rule(self):
        return SanctionsCheckRule()

    def test_sanctioned_fails(self, rule):
        r, score, _ = rule.evaluate({"is_sanctioned": True})
        assert r == RuleResult.FAILED
        assert score == 100

    def test_clean_passes(self, rule):
        r, score, _ = rule.evaluate({"is_sanctioned": False})
        assert r == RuleResult.PASSED
        assert score == 0

    def test_missing_key_defaults_safe(self, rule):
        r, _, _ = rule.evaluate({})
        assert r == RuleResult.PASSED


class TestKYCStatusRule:

    @pytest.fixture()
    def rule(self):
        return KYCStatusRule()

    def test_approved_passes(self, rule):
        r, _, _ = rule.evaluate({"kyc_status": "approved"})
        assert r == RuleResult.PASSED

    def test_pending_warns(self, rule):
        r, score, _ = rule.evaluate({"kyc_status": "pending"})
        assert r == RuleResult.WARNING
        assert score == 40

    def test_rejected_warns_higher(self, rule):
        r, score, _ = rule.evaluate({"kyc_status": "rejected"})
        assert r == RuleResult.WARNING
        assert score == 80


class TestRuleEngine:

    @pytest.fixture()
    def engine(self):
        return RuleEngine()

    def test_clean_context_low_risk(self, engine, clean_context):
        result = engine.evaluate(clean_context)
        assert result["risk_level"] == "low"
        assert result["should_flag"] is False
        assert result["should_block"] is False

    def test_risky_context_flags(self, engine, risky_context):
        result = engine.evaluate(risky_context)
        assert result["risk_level"] in ("high", "critical")
        assert result["should_flag"] is True
        assert len(result["triggered_rules"]) >= 2

    def test_sanctioned_blocks(self, engine, clean_context):
        clean_context["is_sanctioned"] = True
        result = engine.evaluate(clean_context)
        assert result["should_block"] is True

    def test_score_bounded_0_100(self, engine, risky_context):
        risky_context["is_sanctioned"] = True
        result = engine.evaluate(risky_context)
        assert 0 <= result["risk_score"] <= 100

    def test_empty_context_does_not_crash(self, engine):
        result = engine.evaluate({})
        assert "risk_score" in result
        assert "risk_level" in result

    def test_result_keys(self, engine, clean_context):
        result = engine.evaluate(clean_context)
        expected = {"risk_score", "risk_level", "triggered_rules", "should_flag", "should_block"}
        assert expected == set(result.keys())
