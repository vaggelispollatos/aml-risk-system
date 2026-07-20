"""Unit tests for alert endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.db.models.alert import Alert, AlertSeverity, AlertStatus

TEST_DB = "sqlite:///./test_endpoints.db"

engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    from app.db.models.customer import Customer
    from app.db.models.transaction import Transaction
    from app.db.models.alert import Alert
    db = TestingSession()
    try:
        db.query(Alert).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def customer():
    response = client.post("/api/v1/customers", json={
        "name": "Alert Customer",
        "email": f"alert_{uuid.uuid4().hex[:8]}@test.com",
        "country": "US"
    })
    return response.json()


@pytest.fixture()
def alert_id(customer):
    """Create alert directly in DB."""
    db = TestingSession()
    try:
        alert = Alert(
            customer_id=customer["id"],
            transaction_id=None,
            rule_triggered="high_transaction_amount",
            severity=AlertSeverity.HIGH,
            reason="Test alert - amount exceeds threshold",
            status=AlertStatus.OPEN,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        aid = alert.id
        return aid
    finally:
        db.close()


class TestListAlerts:

    def test_list_alerts_empty(self):
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_alerts_with_data(self, alert_id):
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_alerts_filter_by_status(self, alert_id):
        response = client.get("/api/v1/alerts?status=open")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_alerts_filter_by_severity(self, alert_id):
        response = client.get("/api/v1/alerts?severity=high")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_alerts_filter_by_customer(self, customer, alert_id):
        response = client.get(f"/api/v1/alerts?customer_id={customer['id']}")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_alerts_pagination(self):
        response = client.get("/api/v1/alerts?skip=0&limit=10")
        assert response.status_code == 200


class TestGetAlert:

    def test_get_alert_success(self, alert_id):
        response = client.get(f"/api/v1/alerts/{alert_id}")
        assert response.status_code == 200
        assert response.json()["id"] == alert_id

    def test_get_alert_not_found(self):
        response = client.get("/api/v1/alerts/nonexistent-id")
        assert response.status_code == 404


class TestReviewAlert:

    def test_review_alert_resolve(self, alert_id):
        response = client.patch(f"/api/v1/alerts/{alert_id}", json={
            "status": "resolved",
            "review_notes": "Investigated and cleared",
            "reviewed_by": "analyst@company.com",
            "action_taken": "No action required"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["reviewed"] is True

    def test_review_alert_escalate(self, alert_id):
        response = client.patch(f"/api/v1/alerts/{alert_id}", json={
            "status": "escalated",
            "review_notes": "Needs further investigation"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "escalated"

    def test_review_alert_not_found(self):
        response = client.patch("/api/v1/alerts/nonexistent-id", json={
            "status": "resolved"
        })
        assert response.status_code == 404