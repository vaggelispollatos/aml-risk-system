"""Unit tests for compliance officer agent endpoints."""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base
from app.db.models.alert import Alert, AlertSeverity, AlertStatus
from app.db.models.customer import Customer, KYCStatus, RiskLevel

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
    from app.db.models.transaction import Transaction
    from app.db.models.compliance_assessment import ComplianceAssessment
    db = TestingSession()
    try:
        db.query(ComplianceAssessment).delete()
        db.query(Alert).delete()
        db.query(Transaction).delete()
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def customer():
    db = TestingSession()
    try:
        c = Customer(
            name="Compliance Test Customer",
            email=f"compliance_{uuid.uuid4().hex[:8]}@test.com",
            country="US",
            kyc_status=KYCStatus.APPROVED,
            risk_level=RiskLevel.HIGH,
            is_sanctioned=False,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    finally:
        db.close()


@pytest.fixture()
def alert_id(customer):
    db = TestingSession()
    try:
        alert = Alert(
            customer_id=customer.id,
            transaction_id=None,
            rule_triggered="velocity_check",
            severity=AlertSeverity.CRITICAL,
            reason="10 transactions in 60min (limit 5)",
            status=AlertStatus.OPEN,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert.id
    finally:
        db.close()


class TestAssessAlert:

    def test_assess_alert_creates_assessment(self, alert_id):
        response = client.post(f"/api/v1/compliance/alerts/{alert_id}/assess")
        assert response.status_code == 201
        data = response.json()
        assert data["alert_id"] == alert_id
        assert data["recommended_action"] == "file_sar"
        assert data["legal_risk_level"] == "critical"
        assert data["sar_filing_deadline"] is not None
        assert len(data["regulatory_citations"]) > 0
        assert "does not constitute legal advice" in data["narrative"]

    def test_assess_alert_not_found(self):
        response = client.post("/api/v1/compliance/alerts/nonexistent-id/assess")
        assert response.status_code == 404


class TestGetLatestAssessmentForAlert:

    def test_get_latest_assessment(self, alert_id):
        client.post(f"/api/v1/compliance/alerts/{alert_id}/assess")
        response = client.get(f"/api/v1/compliance/alerts/{alert_id}/assessment")
        assert response.status_code == 200
        assert response.json()["alert_id"] == alert_id

    def test_get_latest_assessment_not_found(self, alert_id):
        response = client.get(f"/api/v1/compliance/alerts/{alert_id}/assessment")
        assert response.status_code == 404


class TestListAssessments:

    def test_list_assessments(self, alert_id):
        client.post(f"/api/v1/compliance/alerts/{alert_id}/assess")
        response = client.get("/api/v1/compliance/assessments")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_list_assessments_filter_by_recommended_action(self, alert_id):
        client.post(f"/api/v1/compliance/alerts/{alert_id}/assess")
        response = client.get("/api/v1/compliance/assessments?recommended_action=file_sar")
        assert response.status_code == 200
        assert len(response.json()) >= 1


class TestGetAssessment:

    def test_get_assessment_by_id(self, alert_id):
        created = client.post(f"/api/v1/compliance/alerts/{alert_id}/assess").json()
        response = client.get(f"/api/v1/compliance/assessments/{created['id']}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_assessment_not_found(self):
        response = client.get("/api/v1/compliance/assessments/nonexistent-id")
        assert response.status_code == 404
