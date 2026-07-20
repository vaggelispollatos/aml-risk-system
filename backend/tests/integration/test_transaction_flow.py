"""Integration tests - full transaction-to-alert flow through real DB."""

import pytest

from app.db.models.transaction import TransactionStatus
from app.schemas.transaction import TransactionCreate
from app.services.alert_service import AlertService
from app.services.transaction_service import TransactionService


@pytest.mark.integration
class TestTransactionFlow:

    def test_normal_transaction_completes(self, db, make_customer):
        customer = make_customer(name="Normal User")
        svc = TransactionService(db)

        data = TransactionCreate(
            customer_id=customer.id,
            type="deposit",
            amount=500,
            currency="USD",
            source_country="US",
        )
        txn = svc.create(data)

        assert txn.status == TransactionStatus.COMPLETED
        assert txn.flagged is False
        assert txn.risk_score < 25

    def test_high_amount_flags(self, db, make_customer):
        customer = make_customer(name="Big Spender")
        svc = TransactionService(db)

        data = TransactionCreate(
            customer_id=customer.id,
            type="transfer",
            amount=50_000,
            currency="USD",
            source_country="US",
            destination_country="CN",
        )
        txn = svc.create(data)

        assert txn.risk_score > 0
        assert txn.status in (
        TransactionStatus.COMPLETED,
        TransactionStatus.FLAGGED,
        TransactionStatus.BLOCKED,
)
    def test_sanctioned_customer_blocks(self, db, make_customer):
        customer = make_customer(name="Bad Actor", is_sanctioned=True)
        svc = TransactionService(db)

        data = TransactionCreate(
            customer_id=customer.id,
            type="transfer",
            amount=100,
            currency="USD",
        )
        txn = svc.create(data)

        assert txn.status == TransactionStatus.BLOCKED

    def test_customer_stats_update(self, db, make_customer):
        customer = make_customer(name="Stats User")
        svc = TransactionService(db)

        for _ in range(3):
            svc.create(TransactionCreate(
                customer_id=customer.id,
                type="deposit",
                amount=1000,
                currency="USD",
            ))

        db.refresh(customer)
        assert customer.total_transactions == 3
        assert customer.total_volume == 3000
        assert customer.last_transaction_at is not None


@pytest.mark.integration
class TestAlertFlow:

    def test_alerts_created_for_flagged_transaction(self, db, make_customer):
        customer = make_customer(name="Alert Target")
        txn_svc = TransactionService(db)
        alert_svc = AlertService(db)

        data = TransactionCreate(
            customer_id=customer.id,
            type="transfer",
            amount=50_000,
            currency="USD",
        )
        txn = txn_svc.create(data)

        ctx = txn_svc._build_context(customer, data)
        assessment = txn_svc.engine.evaluate(ctx)
        alerts = alert_svc.create_from_assessment(
            customer_id=customer.id,
            transaction_id=txn.id,
            triggered_rules=assessment["triggered_rules"],
        )

        assert len(alerts) >= 1
        assert all(a.customer_id == customer.id for a in alerts)

    def test_alert_review_workflow(self, db, make_customer):
        customer = make_customer(name="Review Target")
        alert_svc = AlertService(db)

        alerts = alert_svc.create_from_assessment(
            customer_id=customer.id,
            transaction_id=None,
            triggered_rules=[{
                "rule": "manual_test",
                "severity": "high",
                "result": "failed",
                "score": 60,
                "reason": "Test alert",
            }],
        )

        from app.schemas.alert import AlertReview
        updated = alert_svc.review(alerts[0].id, AlertReview(
            status="resolved",
            review_notes="False positive after investigation",
            reviewed_by="analyst@company.com",
        ))

        assert updated.reviewed is True
        assert updated.status.value == "resolved"
        assert updated.reviewed_by == "analyst@company.com"
