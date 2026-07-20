"""Customer CRUD endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import CustomerNotFoundError, DuplicateEmailError
from app.db.models.customer import Customer, KYCStatus
from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    existing = db.query(Customer).filter(Customer.email == data.email).first()
    if existing:
        raise DuplicateEmailError(data.email)

    customer = Customer(
        name=data.name,
        email=data.email,
        phone=data.phone,
        country=data.country.upper(),
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return (
        db.query(Customer)
        .order_by(Customer.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundError(customer_id)
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str, data: CustomerUpdate, db: Session = Depends(get_db)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise CustomerNotFoundError(customer_id)

    if data.name is not None:
        customer.name = data.name
    if data.phone is not None:
        customer.phone = data.phone
    if data.country is not None:
        customer.country = data.country.upper()
    if data.kyc_status is not None:
        customer.kyc_status = KYCStatus(data.kyc_status)

    db.commit()
    db.refresh(customer)
    return customer