"""Transaction processing: ingest → score → persist → alert."""

import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import CustomerNotFoundError
from app.db.models.customer import Customer
from app.db.models.transaction import Transaction, TransactionStatus, TransactionType
from app.schemas.transaction import TransactionCreate
from app.services.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


class TransactionService:

    def __init__(self, db: Session):
        self.db = db
        self.engine = RuleEngine()

    def create(self, data: TransactionCreate) -> Transaction:
        """Ingest a new transaction, score it, and persist."""
        customer = self._get_customer(data.customer_id)
        ctx = self._build_context(customer, data)
        assessment = self.engine.evaluate(ctx)

        status = self._decide_status(assessment)

        txn = Transaction(
            customer_id=data.customer_id,
            type=TransactionType(data.type),
            amount=data.amount,
            currency=data.currency,
            source_country=data.source_country,
            destination_country=data.destination_country,
            risk_score=assessment["risk_score"],
            risk_level=assessment["risk_level"],
            flagged=assessment["should_flag"],
            status=status,
            processed_at=datetime.utcnow(),
        )
        self.db.add(txn)

        customer.total_transactions += 1
        customer.total_volume += data.amount
        customer.last_transaction_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(txn)

        logger.info(
            "Transaction %s scored %.1f (%s) — %s",
            txn.id[:8],
            txn.risk_score,
            txn.risk_level,
            txn.status.value,
        )
        return txn

    def get_by_id(self, txn_id: str) -> Transaction | None:
        return self.db.query(Transaction).filter(Transaction.id == txn_id).first()

    def list_transactions(
        self,
        skip: int = 0,
        limit: int = 50,
        flagged_only: bool = False,
        customer_id: str | None = None,
    ) -> list[Transaction]:
        q = self.db.query(Transaction)
        if flagged_only:
            q = q.filter(Transaction.flagged.is_(True))
        if customer_id:
            q = q.filter(Transaction.customer_id == customer_id)
        return q.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    def _get_customer(self, customer_id: str) -> Customer:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise CustomerNotFoundError(customer_id)
        return customer

    def _build_context(self, customer: Customer, data: TransactionCreate) -> dict:
        """Assemble the dict the rule engine needs."""
        window = datetime.utcnow() - timedelta(minutes=settings.VELOCITY_WINDOW_MINUTES)
        recent_count = (
            self.db.query(Transaction)
            .filter(
                Transaction.customer_id == customer.id,
                Transaction.created_at >= window,
                Transaction.status != TransactionStatus.FAILED,
            )
            .count()
        )

        avg_amount = (
            customer.total_volume / customer.total_transactions
            if customer.total_transactions
            else 0
        )

        last_txn = (
            self.db.query(Transaction)
            .filter(Transaction.customer_id == customer.id)
            .order_by(Transaction.created_at.desc())
            .first()
        )

        return {
            "amount": data.amount,
            "customer_name": customer.name,
            "customer_avg_transaction": avg_amount,
            "recent_transactions_count": recent_count,
            "source_country": data.source_country or customer.country,
            "destination_country": data.destination_country,
            "customer_last_country": (
                last_txn.source_country if last_txn else customer.country
            ),
            "time_since_last_transaction": (
                datetime.utcnow() - last_txn.created_at
                if last_txn
                else timedelta(hours=24)
            ),
            "distance_km": 0,
            "kyc_status": customer.kyc_status.value,
            "is_sanctioned": customer.is_sanctioned,
        }

    @staticmethod
    def _decide_status(assessment: dict) -> TransactionStatus:
        if assessment["should_block"]:
            return TransactionStatus.BLOCKED
        if assessment["should_flag"]:
            return TransactionStatus.FLAGGED
        return TransactionStatus.COMPLETED