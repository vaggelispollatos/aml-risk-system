"""Alert endpoints — list, detail, review."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import AlertNotFoundError
from app.db.session import get_db
from app.schemas.alert import AlertResponse, AlertReview
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
    severity: str | None = Query(None),
    customer_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    svc = AlertService(db)
    return svc.list_alerts(skip, limit, status, severity, customer_id)


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    svc = AlertService(db)
    alert = svc.get_by_id(alert_id)
    if not alert:
        raise AlertNotFoundError(alert_id)
    return alert


@router.patch("/{alert_id}", response_model=AlertResponse)
def review_alert(
    alert_id: str, payload: AlertReview, db: Session = Depends(get_db)
):
    svc = AlertService(db)
    alert = svc.review(alert_id, payload)
    if not alert:
        raise AlertNotFoundError(alert_id)
    return alert