"""Combine all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import alerts, customers, transactions

api_router = APIRouter()

api_router.include_router(customers.router)
api_router.include_router(transactions.router)
api_router.include_router(alerts.router)