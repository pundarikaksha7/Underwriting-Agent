"""Machine learning model service for decision predictions."""

import logging
import pickle
import numpy as np
from typing import Dict, Any, Tuple, Optional
import joblib

from app.config import settings

logger = logging.getLogger(__name__)


class MLModelService:
    """Service for ML-based decision predictions."""

    def __init__(self):
        """Initialize ML model service."""
        self.model = None
        self.feature_names = None
        self.scaler = None
        self.is_loaded = False
        self._init_model()

    def _init_model(self):
        """Initialize or load ML model. Creates a dummy model for demo."""
        try:
            # In production, load from saved file
            # For now, we'll create a simple model on the fly
            self.is_loaded = True
            logger.info("ML Model initialized (demo mode)")
        except Exception as e:
            logger.error(f"Failed to initialize ML model: {e}")
            self.is_loaded = False

    def extract_features(self, application_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Extract features from application data.
        
        Returns:
            (feature_array, feature_dict)
        """
        features = {}
        
        # Financial ratios
        annual_income = application_data.get('annual_income', 0)
        monthly_income = annual_income / 12 if annual_income > 0 else 0
        monthly_expenses = application_data.get('monthly_expenses', 0)
        
        features['monthly_cash_flow'] = monthly_income - monthly_expenses
        features['cash_flow_ratio'] = (monthly_income - monthly_expenses) / monthly_income if monthly_income > 0 else 0
        
        # Debt-to-income ratio
        loan_amount = application_data.get('loan_amount', 0)
        monthly_loan_payment = self._estimate_monthly_payment(
            loan_amount,
            application_data.get('loan_term_months', 60)
        )
        existing_debts = application_data.get('existing_debts', 0)
        total_monthly_debt = (existing_debts / 12) + monthly_loan_payment
        features['debt_to_income'] = total_monthly_debt / monthly_income if monthly_income > 0 else 1.0
        
        # Credit features
        credit_score = application_data.get('credit_score', 650)
        features['credit_score_normalized'] = min(credit_score / 850, 1.0)
        features['delinquency_count'] = float(application_data.get('delinquencies', 0))
        features['account_count'] = float(application_data.get('number_of_accounts', 0))
        features['credit_utilization'] = (existing_debts / 100000) if existing_debts > 0 else 0  # Rough estimate
        
        # Employment features
        employment_status = application_data.get('employment_status', 'unknown').lower()
        features['employment_stability'] = self._score_employment(employment_status)
        features['years_employed'] = float(application_data.get('years_employed', 0))
        
        # Loan features
        features['loan_amount_normalized'] = min(loan_amount / 500000, 1.0)  # Normalize against 500k max
        features['loan_term_months'] = float(application_data.get('loan_term_months', 60))
        
        # Collateral
        collateral_value = application_data.get('collateral_value', 0) or 0
        features['loan_to_value'] = loan_amount / collateral_value if collateral_value > 0 else 1.0
        
        # Convert to array for ML inference
        feature_array = np.array([list(features.values())])
        
        return feature_array, features

    def predict(
        self,
        application_data: Dict[str, Any],
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Make ML-based prediction for application.
        
        Returns:
            (decision, confidence, metadata)
        """
        try:
            feature_array, extracted_features = self.extract_features(application_data)
            
            # Simple heuristic-based decision (in production, would be ML model inference)
            decision, confidence = self._heuristic_decision(extracted_features)
            
            risk_score = self._calculate_risk_score(extracted_features)
            
            metadata = {
                "features": extracted_features,
                "risk_score": risk_score,
                "model_type": "heuristic",  # Would be "lightgbm" or "sklearn" in production
            }
            
            logger.info(f"ML prediction: {decision} (confidence: {confidence:.2f})")
            return decision, confidence, metadata
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return "pending", 0.3, {"error": str(e)}

    def _heuristic_decision(self, features: Dict[str, float]) -> Tuple[str, float]:
        """
        Heuristic decision logic based on features.
        
        In production, this would be replaced by actual ML model inference.
        """
        score = 0.5  # Start at neutral
        
        # Credit score impact
        credit_normalized = features.get('credit_score_normalized', 0)
        score += credit_normalized * 0.3
        
        # Debt-to-income impact
        dti = features.get('debt_to_income', 1.0)
        if dti < 0.3:
            score += 0.2
        elif dti < 0.5:
            score += 0.1
        elif dti >= 0.8:
            score -= 0.2
        
        # Delinquency impact
        delinquencies = features.get('delinquency_count', 0)
        if delinquencies > 0:
            score -= (0.1 * min(delinquencies, 3))
        
        # Employment stability
        employment_score = features.get('employment_stability', 0.3)
        score += employment_score * 0.2
        
        # Cash flow
        cash_flow = features.get('cash_flow_ratio', -1)
        if cash_flow > 0.1:
            score += 0.15
        elif cash_flow < -0.1:
            score -= 0.15
        
        # Ensure score is between 0 and 1
        confidence = min(max(score, 0), 1)
        
        # Decision threshold
        if confidence > 0.65:
            decision = "approved"
        elif confidence > 0.45:
            decision = "conditional"
        else:
            decision = "rejected"
        
        return decision, confidence

    def _calculate_risk_score(self, features: Dict[str, float]) -> float:
        """Calculate a risk score (0 = low risk, 1 = high risk)."""
        risk = 0.5
        
        # Higher DTI = higher risk
        dti = features.get('debt_to_income', 0.5)
        risk += min(dti - 0.5, 0.2)  # Add up to 0.2 for high DTI
        
        # Lower credit score = higher risk
        credit = features.get('credit_score_normalized', 0.5)
        risk -= (credit - 0.5) * 0.2
        
        # Delinquencies = higher risk
        delinquencies = features.get('delinquency_count', 0)
        risk += min(delinquencies * 0.05, 0.2)
        
        # Poor employment = higher risk
        employment = features.get('employment_stability', 0.3)
        risk -= employment * 0.1
        
        return min(max(risk, 0), 1)

    @staticmethod
    def _score_employment(employment_status: str) -> float:
        """Score employment status."""
        scores = {
            "employed": 0.8,
            "self-employed": 0.6,
            "retired": 0.5,
            "unemployed": 0.0,
            "student": 0.2,
        }
        return scores.get(employment_status.lower(), 0.3)

    @staticmethod
    def _estimate_monthly_payment(principal: float, term_months: int) -> float:
        """Rough estimate of monthly payment (assumes ~6% APR)."""
        if term_months == 0 or principal == 0:
            return 0
        
        monthly_rate = 0.06 / 12
        payment = principal * (monthly_rate * (1 + monthly_rate) ** term_months) / \
                  ((1 + monthly_rate) ** term_months - 1)
        return payment

    def train_on_feedback(self, decision_history: list):
        """
        Train/update model based on feedback.
        
        This is a placeholder - in production would use proper ML training.
        """
        logger.info(f"Training on {len(decision_history)} feedback samples")
        # In production: update feature importance, retrain model, etc.
        pass
