"""Decision endpoints."""

import logging
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.models.db import Application, Decision
from app.models.schemas import (
    UnderwritingRequest,
    UnderwritingResponse,
    DecisionResponse,
    DecisionFeedback,
)
from app.services.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["decisions"])

# Initialize decision engine
decision_engine = DecisionEngine()


@router.post("/underwrite", response_model=UnderwritingResponse, status_code=status.HTTP_200_OK)
async def underwrite_application(
    request: UnderwritingRequest,
    db: Session = Depends(get_db),
    force_model: Optional[str] = None,
):
    """
    Make underwriting decision for an application.
    
    This is the main endpoint that:
    1. Takes application data
    2. Runs ML model
    3. Routes to appropriate LLM if needed
    4. Returns decision with explanation
    """
    try:
        # Create application in DB
        app_data = request.application
        application = Application(
            applicant_id=1,
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
        
        # Convert to dict for decision engine
        app_dict = {
            "full_name": app_data.full_name,
            "email": app_data.email,
            "phone": app_data.phone,
            "date_of_birth": app_data.date_of_birth,
            "gender": app_data.gender,
            "street_address": app_data.street_address,
            "city": app_data.city,
            "state": app_data.state,
            "postal_code": app_data.postal_code,
            "country": app_data.country,
            "annual_income": app_data.annual_income,
            "monthly_expenses": app_data.monthly_expenses,
            "employment_status": app_data.employment_status,
            "years_employed": app_data.years_employed,
            "employer": app_data.employer,
            "credit_score": app_data.credit_score,
            "existing_debts": app_data.existing_debts,
            "number_of_accounts": app_data.number_of_accounts,
            "delinquencies": app_data.delinquencies,
            "loan_amount": app_data.loan_amount,
            "loan_term_months": app_data.loan_term_months,
            "loan_purpose": app_data.loan_purpose,
            "collateral_value": app_data.collateral_value,
            "applicant_notes": app_data.applicant_notes,
            "additional_data": app_data.additional_data,
        }
        
        # Make decision
        response, metadata = await decision_engine.make_decision(
            application_data=app_dict,
            db=db,
            application_id=application.id,
            force_model=force_model or request.force_model,
            include_rag=request.include_rag or False,
        )
        
        # Update application status based on decision
        if response.decision == "approved":
            application.status = "approved"
        elif response.decision == "rejected":
            application.status = "rejected"
        else:
            application.status = "under_review"
        
        db.commit()
        
        logger.info(f"Decision made for application {application.id}: {response.decision}")
        return response
        
    except Exception as e:
        logger.error(f"Underwriting error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Underwriting failed: {str(e)}",
        )


@router.post("/{decision_id}/feedback", status_code=status.HTTP_200_OK)
async def provide_feedback(
    decision_id: int,
    feedback: DecisionFeedback,
    db: Session = Depends(get_db),
):
    """
    Provide feedback on a decision for model improvement.
    
    This enables the system to learn from outcomes and improve over time.
    """
    try:
        decision = db.query(Decision).filter(Decision.id == decision_id).first()
        
        if not decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Decision {decision_id} not found",
            )
        
        is_correct = feedback.feedback == "correct"
        decision_engine.record_feedback(
            decision_id=decision_id,
            is_correct=is_correct,
            db=db,
        )
        
        logger.info(f"Feedback recorded for decision {decision_id}: {feedback.feedback}")
        
        return {
            "message": "Feedback recorded successfully",
            "decision_id": decision_id,
            "feedback": feedback.feedback,
        }
        
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}",
        )


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific decision."""
    decision = db.query(Decision).filter(Decision.id == decision_id).first()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found",
        )
    
    return decision
