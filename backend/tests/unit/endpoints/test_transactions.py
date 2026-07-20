"""Unit tests for transaction endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import get_db
from app.db.base import Base

TEST_DB = "sqlite:///./test_endpoints.db"

engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    Base.metadata.create_all(bind=engine)
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
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def customer():
    response = client.post("/api/v1/customers", json={
        "name": "Test Customer",
        "email": "txn_customer@test.com",
        "country": "US"
    })
    return response.json()


class TestCreateTransaction:

    def test_create_normal_transaction(self, customer):
        response = client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "deposit",
            "amount": 500,
            "currency": "USD",
            "source_country": "US"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 500
        assert data["status"] == "completed"
        assert data["flagged"] is False

    def test_create_high_amount_transaction(self, customer):
        response = client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "transfer",
            "amount": 50000,
            "currency": "USD",
            "source_country": "US",
            "destination_country": "CN"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["risk_score"] > 0

    def test_create_transaction_invalid_type(self, customer):
        response = client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "invalid_type",
            "amount": 500,
            "currency": "USD"
        })
        assert response.status_code == 422

    def test_create_transaction_negative_amount(self, customer):
        response = client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "deposit",
            "amount": -100,
            "currency": "USD"
        })
        assert response.status_code == 422

    def test_create_transaction_invalid_customer(self):
        response = client.post("/api/v1/transactions", json={
            "customer_id": "nonexistent-id",
            "type": "deposit",
            "amount": 500,
            "currency": "USD"
        })
        assert response.status_code == 404


class TestGetTransaction:

    def test_get_transaction_success(self, customer):
        create = client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "deposit",
            "amount": 500,
            "currency": "USD"
        })
        txn_id = create.json()["id"]

        response = client.get(f"/api/v1/transactions/{txn_id}")
        assert response.status_code == 200
        assert response.json()["id"] == txn_id

    def test_get_transaction_not_found(self):
        response = client.get("/api/v1/transactions/nonexistent-id")
        assert response.status_code == 404


class TestListTransactions:

    def test_list_transactions(self, customer):
        client.post("/api/v1/transactions", json={
            "customer_id": customer["id"],
            "type": "deposit",
            "amount": 500,
            "currency": "USD"
        })
        response = client.get("/api/v1/transactions")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_transactions_flagged_only(self, customer):
        response = client.get("/api/v1/transactions?flagged_only=true")
        assert response.status_code == 200

    def test_list_transactions_by_customer(self, customer):
        response = client.get(f"/api/v1/transactions?customer_id={customer['id']}")
        assert response.status_code == 200
