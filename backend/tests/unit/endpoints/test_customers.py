"""Unit tests for customer endpoints."""

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


class TestCreateCustomer:

    def test_create_customer_success(self):
        response = client.post("/api/v1/customers", json={
            "name": "John Doe",
            "email": "john@test.com",
            "country": "US"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "john@test.com"
        assert data["name"] == "John Doe"
        assert data["risk_level"] == "low"

    def test_create_customer_duplicate_email(self):
        client.post("/api/v1/customers", json={
            "name": "John Doe",
            "email": "duplicate@test.com",
            "country": "US"
        })
        response = client.post("/api/v1/customers", json={
            "name": "Jane Doe",
            "email": "duplicate@test.com",
            "country": "US"
        })
        assert response.status_code == 409

    def test_create_customer_invalid_email(self):
        response = client.post("/api/v1/customers", json={
            "name": "John Doe",
            "email": "not-an-email",
            "country": "US"
        })
        assert response.status_code == 422

    def test_create_customer_missing_country(self):
        response = client.post("/api/v1/customers", json={
            "name": "John Doe",
            "email": "john2@test.com",
        })
        assert response.status_code == 422


class TestGetCustomer:

    def test_get_customer_success(self):
        create = client.post("/api/v1/customers", json={
            "name": "Jane Doe",
            "email": "jane@test.com",
            "country": "GB"
        })
        customer_id = create.json()["id"]

        response = client.get(f"/api/v1/customers/{customer_id}")
        assert response.status_code == 200
        assert response.json()["id"] == customer_id

    def test_get_customer_not_found(self):
        response = client.get("/api/v1/customers/nonexistent-id")
        assert response.status_code == 404


class TestListCustomers:

    def test_list_customers(self):
        client.post("/api/v1/customers", json={
            "name": "User One",
            "email": "one@test.com",
            "country": "US"
        })
        response = client.get("/api/v1/customers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) >= 1

    def test_list_customers_pagination(self):
        response = client.get("/api/v1/customers?skip=0&limit=10")
        assert response.status_code == 200


class TestUpdateCustomer:

    def test_update_customer_success(self):
        create = client.post("/api/v1/customers", json={
            "name": "Old Name",
            "email": "update@test.com",
            "country": "US"
        })
        customer_id = create.json()["id"]

        response = client.patch(f"/api/v1/customers/{customer_id}", json={
            "name": "New Name"
        })
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_update_customer_not_found(self):
        response = client.patch("/api/v1/customers/nonexistent-id", json={
            "name": "New Name"
        })
        assert response.status_code == 404

    def test_update_kyc_status(self):
        create = client.post("/api/v1/customers", json={
            "name": "KYC User",
            "email": "kyc@test.com",
            "country": "US"
        })
        customer_id = create.json()["id"]

        response = client.patch(f"/api/v1/customers/{customer_id}", json={
            "kyc_status": "approved"
        })
        assert response.status_code == 200
        assert response.json()["kyc_status"] == "approved"