"""Application management endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.db import Application, User
from app.models.schemas import ApplicationCreate, ApplicationResponse, ApplicationUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    app_data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new application.
    
    Accepts full applicant and loan information.
    """
    try:
        # In production, would verify applicant identity
        
        application = Application(
            applicant_id=1,  # Placeholder
            reference_number=f"APP-{hash(app_data.email) % 100000}",
            full_name=app_data.full_name,
            email=app_data.email,
            phone=app_data.phone,
            date_of_birth=app_data.date_of_birth,
            gender=app_data.gender,
            street_address=app_data.street_address,
            city=app_data.city,
            state=app_data.state,
            postal_code=app_data.postal_code,
            country=app_data.country,
            annual_income=app_data.annual_income,
            monthly_expenses=app_data.monthly_expenses,
            employment_status=app_data.employment_status,
            years_employed=app_data.years_employed,
            employer=app_data.employer,
            credit_score=app_data.credit_score,
            existing_debts=app_data.existing_debts,
            number_of_accounts=app_data.number_of_accounts,
            delinquencies=app_data.delinquencies,
            loan_amount=app_data.loan_amount,
            loan_term_months=app_data.loan_term_months,
            loan_purpose=app_data.loan_purpose,
            collateral_value=app_data.collateral_value,
            applicant_notes=app_data.applicant_notes,
            additional_data=app_data.additional_data,
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        logger.info(f"Application created: {application.reference_number}")
        return application
        
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create application: {str(e)}",
        )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    """Get application by ID."""
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    
    return application


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    app_update: ApplicationUpdate,
    db: Session = Depends(get_db),
):
    """Update application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application {application_id} not found",
        )
    
    update_data = app_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)
    
    db.commit()
    db.refresh(application)
    
    logger.info(f"Application updated: {application.id}")
    return application


@router.get("/", response_model=List[ApplicationResponse])
async def list_applications(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    db: Session = Depends(get_db),
):
    """List applications with optional filtering."""
    query = db.query(Application)
    
    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    applications = query.offset(skip).limit(limit).all()
    return applications
