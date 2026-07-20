"""Transaction endpoints — ingest and query."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import TransactionNotFoundError
from app.db.session import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.alert_service import AlertService
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    svc = TransactionService(db)
    txn = svc.create(data)

    # Generate alerts for flagged/blocked transactions
    if txn.flagged:
        alert_svc = AlertService(db)
        ctx = svc._build_context(txn.customer, data)
        assessment = svc.engine.evaluate(ctx)
        alert_svc.create_from_assessment(
            customer_id=txn.customer_id,
            transaction_id=txn.id,
            triggered_rules=assessment["triggered_rules"],
        )

    return txn


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    flagged_only: bool = Query(False),
    customer_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    svc = TransactionService(db)
    return svc.list_transactions(skip, limit, flagged_only, customer_id)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    svc = TransactionService(db)
    txn = svc.get_by_id(transaction_id)
    if not txn:
        raise TransactionNotFoundError(transaction_id)
    return txn