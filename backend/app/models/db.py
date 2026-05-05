"""Database models for the underwriting system."""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Boolean, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class User(Base):
    """User/Applicant model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default="applicant")  # applicant, underwriter, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applications = relationship("Application", back_populates="applicant")
    decisions = relationship("Decision", back_populates="user")


class Application(Base):
    """Credit application model."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), index=True)
    reference_number = Column(String(255), unique=True, index=True)

    # Applicant Info
    full_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(20))
    date_of_birth = Column(String(10))
    gender = Column(String(10))
    
    # Address
    street_address = Column(String(255))
    city = Column(String(100))
    state = Column(String(50))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Financial Information
    annual_income = Column(Float)
    monthly_expenses = Column(Float)
    employment_status = Column(String(50))  # employed, self-employed, retired, etc.
    years_employed = Column(Float)
    employer = Column(String(255))
    
    # Credit Information
    credit_score = Column(Integer)
    existing_debts = Column(Float)
    number_of_accounts = Column(Integer)
    delinquencies = Column(Integer)
    
    # Loan Request
    loan_amount = Column(Float)
    loan_term_months = Column(Integer)
    loan_purpose = Column(String(100))
    collateral_value = Column(Float, nullable=True)
    
    # Additional Context (unstructured)
    applicant_notes = Column(Text, nullable=True)
    
    # Additional structured fields
    additional_data = Column(JSON, nullable=True)
    
    status = Column(String(50), default="submitted")  # submitted, under_review, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    applicant = relationship("User", back_populates="applications")
    decision = relationship("Decision", back_populates="application", uselist=False)
    decision_history = relationship("DecisionHistory", back_populates="application")


class DecisionStatus(str, enum.Enum):
    """Decision status enum."""
    APPROVED = "approved"
    REJECTED = "rejected"
    PENDING = "pending"
    CONDITIONAL = "conditional"


class Decision(Base):
    """Decision record model."""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    decision = Column(String(50), index=True)  # approved, rejected, conditional, pending
    confidence = Column(Float)
    risk_score = Column(Float)
    
    # LLM and Model Info
    primary_model_used = Column(String(100))  # gpt-4, gpt-3.5-turbo, local, ensemble
    reasoning = Column(Text)
    explanation = Column(Text)
    
    # Routing Info
    routing_decision = Column(JSON)  # stores router decision details
    rag_used = Column(Boolean, default=False)
    
    # Resource Usage
    latency_ms = Column(Float)
    total_tokens_used = Column(Integer)
    estimated_cost = Column(Float)
    
    # Decision Details
    decision_details = Column(JSON)
    approved_amount = Column(Float, nullable=True)
    offered_interest_rate = Column(Float, nullable=True)
    
    # Feedback
    feedback = Column(String(50), nullable=True)  # correct, incorrect, null=waiting
    feedback_provided_at = Column(DateTime, nullable=True)
    actual_outcome = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="decision")
    user = relationship("User", back_populates="decisions")
    model_metrics = relationship("ModelMetrics", back_populates="decision")


class DecisionHistory(Base):
    """Historical record of all decision attempts for an application."""
    __tablename__ = "decision_history"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), index=True)
    
    model_used = Column(String(100))
    decision = Column(String(50))
    confidence = Column(Float)
    reasoning = Column(Text, nullable=True)
    reasoning_tokens = Column(Integer)
    latency_ms = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="decision_history")


class ModelMetrics(Base):
    """Track model performance metrics."""
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("decisions.id"), index=True)
    
    model_name = Column(String(100), index=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    
    # Latency metrics
    p50_latency = Column(Float, nullable=True)
    p95_latency = Column(Float, nullable=True)
    p99_latency = Column(Float, nullable=True)
    
    # Cost metrics
    total_tokens = Column(Integer)
    approximate_cost = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    decision = relationship("Decision", back_populates="model_metrics")


class RouterLog(Base):
    """Log routing decisions for analysis."""
    __tablename__ = "router_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    decision_id = Column(Integer, ForeignKey("decisions.id"), nullable=True, index=True)
    
    # Routing Info
    selected_model = Column(String(100))
    alternative_models = Column(JSON)
    use_rag = Column(Boolean)
    reasoning = Column(Text)
    
    # Feature values
    input_complexity = Column(Float)
    confidence_threshold_met = Column(Boolean)
    time_budget = Column(Float)
    cost_budget = Column(Float)
    
    # Actual outcome
    actual_latency = Column(Float)
    actual_cost = Column(Float)
    actual_accuracy = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BanditArm(Base):
    """Contextual bandit arms for model selection."""
    __tablename__ = "bandit_arms"

    id = Column(Integer, primary_key=True, index=True)
    
    model_name = Column(String(100), unique=True, index=True)
    model_type = Column(String(50))  # llm, ml, ensemble, rule_based
    
    # LinUCB parameters
    estimated_reward = Column(Float, default=0.5)
    uncertainty = Column(Float, default=1.0)
    num_selections = Column(Integer, default=0)
    num_successes = Column(Integer, default=0)
    
    # Thompson Sampling parameters
    alpha = Column(Float, default=1.0)  # successes + 1
    beta = Column(Float, default=1.0)   # failures + 1
    
    # Cost and latency
    avg_cost = Column(Float, default=0.0)
    avg_latency = Column(Float, default=0.0)
    
    enabled = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureStore(Base):
    """Store computed features for fast retrieval."""
    __tablename__ = "feature_store"

    id = Column(Integer, primary_key=True, index=True)
    
    application_id = Column(Integer, ForeignKey("applications.id"), unique=True, index=True)
    
    # Computed features
    debt_to_income_ratio = Column(Float)
    credit_utilization = Column(Float)
    payment_history_score = Column(Float)
    employability_score = Column(Float)
    risk_category = Column(String(50))
    
    # Normalized features
    normalized_features = Column(JSON)
    
    # Feature computation metadata
    computation_timestamp = Column(DateTime, default=datetime.utcnow)
    is_stale = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RAGDocument(Base):
    """Store documents for RAG system."""
    __tablename__ = "rag_documents"

    id = Column(Integer, primary_key=True, index=True)
    
    title = Column(String(255))
    content = Column(Text)
    category = Column(String(100))  # regulation, policy, case_study, decision_guide
    
    # Vector embedding (stored as JSON for simplicity)
    embedding = Column(JSON, nullable=True)
    
    metadata = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
