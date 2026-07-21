"""Compliance Officer Agent endpoints — run and query legal/regulatory opinions."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import ComplianceAssessmentNotFoundError
from app.db.session import get_db
from app.schemas.compliance_officer import ComplianceAssessmentResponse
from app.services.compliance_service import ComplianceService

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.post(
    "/alerts/{alert_id}/assess",
    response_model=ComplianceAssessmentResponse,
    status_code=201,
)
def assess_alert(alert_id: str, db: Session = Depends(get_db)):
    """Run the Compliance Officer Agent against an alert and persist the opinion."""
    svc = ComplianceService(db)
    return svc.assess_alert(alert_id)


@router.get("/alerts/{alert_id}/assessment", response_model=ComplianceAssessmentResponse)
def get_latest_assessment_for_alert(alert_id: str, db: Session = Depends(get_db)):
    svc = ComplianceService(db)
    assessment = svc.get_latest_for_alert(alert_id)
    if not assessment:
        raise ComplianceAssessmentNotFoundError(alert_id)
    return assessment


@router.get("/assessments", response_model=list[ComplianceAssessmentResponse])
def list_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    recommended_action: str | None = Query(None),
    legal_risk_level: str | None = Query(None),
    customer_id: str | None = Query(None),
    db: Session = Depends(get_db),
):
    svc = ComplianceService(db)
    return svc.list_assessments(skip, limit, recommended_action, legal_risk_level, customer_id)


@router.get("/assessments/{assessment_id}", response_model=ComplianceAssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    svc = ComplianceService(db)
    assessment = svc.get_by_id(assessment_id)
    if not assessment:
        raise ComplianceAssessmentNotFoundError(assessment_id)
    return assessment
