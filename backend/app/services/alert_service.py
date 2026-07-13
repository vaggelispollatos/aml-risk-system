"""Alert lifecycle: create from rule violations, list, review."""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.schemas.alert import AlertReview

logger = logging.getLogger(__name__)


class AlertService:

    def __init__(self, db: Session):
        self.db = db

    def create_from_assessment(
        self,
        customer_id: str,
        transaction_id: str,
        triggered_rules: list[dict],
    ) -> list[Alert]:
        """Create one alert per triggered rule."""
        alerts: list[Alert] = []
        for rule_info in triggered_rules:
            alert = Alert(
                customer_id=customer_id,
                transaction_id=transaction_id,
                rule_triggered=rule_info["rule"],
                severity=AlertSeverity(rule_info["severity"]),
                reason=rule_info["reason"],
            )
            self.db.add(alert)
            alerts.append(alert)

        if alerts:
            self.db.commit()
            for a in alerts:
                self.db.refresh(a)
            logger.info(
                "Created %d alert(s) for customer %s", len(alerts), customer_id
            )

        return alerts

    def get_by_id(self, alert_id: str) -> Alert | None:
        return self.db.query(Alert).filter(Alert.id == alert_id).first()

    def list_alerts(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        severity: str | None = None,
        customer_id: str | None = None,
    ) -> list[Alert]:
        q = self.db.query(Alert)
        if status:
            q = q.filter(Alert.status == AlertStatus(status))
        if severity:
            q = q.filter(Alert.severity == AlertSeverity(severity))
        if customer_id:
            q = q.filter(Alert.customer_id == customer_id)
        return q.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    def review(self, alert_id: str, payload: AlertReview) -> Alert | None:
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        if payload.status:
            alert.status = AlertStatus(payload.status)
        if payload.review_notes:
            alert.review_notes = payload.review_notes
        if payload.action_taken:
            alert.action_taken = payload.action_taken
        if payload.reviewed_by:
            alert.reviewed_by = payload.reviewed_by

        alert.reviewed = True
        alert.reviewed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(alert)
        return alert