"""Shared fixtures for all tests."""

import os
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models.customer import Customer, KYCStatus, RiskLevel
from app.db.models.transaction import Transaction, TransactionStatus, TransactionType

TEST_DB = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture()
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def make_customer(db):
    """Factory: create and persist a Customer."""
    def _make(
        name="Test User",
        email=None,
        country="US",
        kyc_status=KYCStatus.APPROVED,
        is_sanctioned=False,
    ):
        c = Customer(
            name=name,
            email=email or f"{uuid.uuid4().hex[:8]}@test.com",
            country=country,
            kyc_status=kyc_status,
            kyc_date=datetime.utcnow(),
            risk_level=RiskLevel.LOW,
            is_sanctioned=is_sanctioned,
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return c
    return _make


@pytest.fixture()
def make_transaction(db):
    """Factory: create and persist a Transaction."""
    def _make(
        customer_id,
        amount=1000.0,
        type_=TransactionType.TRANSFER,
        source_country="US",
        destination_country="US",
        status=TransactionStatus.COMPLETED,
    ):
        t = Transaction(
            customer_id=customer_id,
            type=type_,
            amount=amount,
            currency="USD",
            source_country=source_country,
            destination_country=destination_country,
            status=status,
            processed_at=datetime.utcnow(),
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return t
    return _make


@pytest.fixture()
def clean_context():
    """A transaction context that should pass all rules."""
    return {
        "amount": 500,
        "customer_avg_transaction": 600,
        "recent_transactions_count": 1,
        "source_country": "US",
        "customer_last_country": "US",
        "time_since_last_transaction": timedelta(hours=12),
        "distance_km": 0,
        "customer_name": "Clean User",
        "kyc_status": "approved",
        "is_sanctioned": False,
    }


@pytest.fixture()
def risky_context():
    """A transaction context that should trigger multiple rules."""
    return {
        "amount": 25000,
        "customer_avg_transaction": 800,
        "recent_transactions_count": 10,
        "source_country": "US",
        "customer_last_country": "CN",
        "time_since_last_transaction": timedelta(minutes=30),
        "distance_km": 12000,
        "customer_name": "Risky User",
        "kyc_status": "pending",
        "is_sanctioned": False,
    }