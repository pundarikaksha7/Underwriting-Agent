"""Pydantic schemas for request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import enum


class DecisionEnum(str, enum.Enum):
    """Decision outcome enum."""
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"
    PENDING = "pending"


class FeedbackEnum(str, enum.Enum):
    """Feedback on decision correctness."""
    CORRECT = "correct"
    INCORRECT = "incorrect"


# ============ Application Schemas ============

class ApplicationBase(BaseModel):
    """Base application schema."""
    full_name: str
    email: EmailStr
    phone: str
    date_of_birth: str
    gender: str
    
    # Address
    street_address: str
    city: str
    state: str
    postal_code: str
    country: str
    
    # Financial
    annual_income: float
    monthly_expenses: float
    employment_status: str
    years_employed: float
    employer: str
    
    # Credit
    credit_score: int = Field(ge=300, le=850)
    existing_debts: float
    number_of_accounts: int
    delinquencies: int = Field(ge=0)
    
    # Loan Request
    loan_amount: float
    loan_term_months: int
    loan_purpose: str
    collateral_value: Optional[float] = None
    
    # Notes
    applicant_notes: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class ApplicationCreate(ApplicationBase):
    """Application creation schema."""
    pass


class ApplicationUpdate(BaseModel):
    """Application update schema."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    annual_income: Optional[float] = None
    credit_score: Optional[int] = None
    applicant_notes: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class ApplicationResponse(ApplicationBase):
    """Application response schema."""
    id: int
    reference_number: str
    applicant_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Decision Schemas ============

class DecisionBase(BaseModel):
    """Base decision schema."""
    decision: str
    confidence: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    reasoning: Optional[str] = None
    explanation: Optional[str] = None


class DecisionResponse(DecisionBase):
    """Decision response schema."""
    id: int
    application_id: int
    primary_model_used: str
    latency_ms: float
    total_tokens_used: int
    estimated_cost: float
    approved_amount: Optional[float] = None
    offered_interest_rate: Optional[float] = None
    rag_used: bool
    routing_decision: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DecisionFeedback(BaseModel):
    """Feedback on a decision."""
    decision_id: int
    feedback: FeedbackEnum
    actual_outcome: Optional[Dict[str, Any]] = None


# ============ Underwriting Request/Response ============

class UnderwritingRequest(BaseModel):
    """Main request for underwriting decision."""
    application: ApplicationCreate
    include_rag: Optional[bool] = False
    simulate: Optional[bool] = False
    force_model: Optional[str] = None  # Force specific model for testing


class UnderwritingResponse(BaseModel):
    """Response from underwriting system."""
    decision_id: int
    application_id: int
    decision: str
    confidence: float
    risk_score: float
    approved_amount: Optional[float] = None
    offered_interest_rate: Optional[float] = None
    reasoning: str
    explanation: str
    model_used: str
    latency_ms: float
    total_tokens_used: int
    estimated_cost: float
    rag_used: bool
    routing_details: Optional[Dict[str, Any]] = None


# ============ Model Metrics Schemas ============

class ModelMetricsResponse(BaseModel):
    """Model metrics response."""
    model_name: str
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    p50_latency: Optional[float]
    p95_latency: Optional[float]
    p99_latency: Optional[float]
    total_tokens: int
    approximate_cost: float

    class Config:
        from_attributes = True


# ============ Analytics Schemas ============

class RoutingAnalytics(BaseModel):
    """Analytics for routing decisions."""
    total_decisions: int
    model_distribution: Dict[str, int]
    avg_latency_by_model: Dict[str, float]
    avg_cost_by_model: Dict[str, float]
    decision_distribution: Dict[str, int]
    avg_confidence: float


class BanditMetrics(BaseModel):
    """Bandit algorithm metrics."""
    model_name: str
    num_selections: int
    num_successes: int
    estimated_reward: float
    uncertainty: float
    avg_cost: float
    avg_latency: float


# ============ User Schemas ============

class UserBase(BaseModel):
    """Base user schema."""
    username: str
    email: EmailStr
    role: str = "applicant"


class UserCreate(UserBase):
    """User creation schema."""
    password: str


class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response."""
    access_token: str
    token_type: str
    user: UserResponse


# ============ Simulation Schemas ============

class SimulationRequest(BaseModel):
    """Request for simulation/training data generation."""
    num_samples: int = Field(default=100, ge=1, le=10000)
    risk_levels: List[str] = ["low", "medium", "high"]  # Distribution of risk levels


class SimulationDataResponse(BaseModel):
    """Response with simulated data."""
    num_generated: int
    applications: List[ApplicationResponse]
    message: str
