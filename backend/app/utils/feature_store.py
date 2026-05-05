"""Feature store service for caching and managing features."""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.db import FeatureStore, Application
from app.services.ml_service import MLModelService

logger = logging.getLogger(__name__)


class FeatureStoreService:
    """Service for storing and retrieving features."""

    def __init__(self):
        """Initialize feature store service."""
        self.ml_service = MLModelService()

    def compute_and_store_features(
        self,
        application_id: int,
        application_data: Dict[str, Any],
        db: Session,
    ) -> FeatureStore:
        """
        Compute features for an application and store in feature store.
        
        Returns:
            FeatureStore object
        """
        try:
            # Extract features
            _, features = self.ml_service.extract_features(application_data)
            
            # Compute derived features
            dti = features.get('debt_to_income', 0.5)
            credit_util = features.get('credit_utilization', 0.0)
            payment_history = 1.0 - min(features.get('delinquency_count', 0) / 5, 1.0)
            employability = features.get('employment_stability', 0.3) * \
                           min(features.get('years_employed', 1) / 10, 1.0)
            
            # Risk categorization
            risk_score = 1.0 - features.get('credit_score_normalized', 0.5)
            if dti > 0.5:
                risk_score += 0.1
            if risk_score < 0.3:
                risk_category = "low_risk"
            elif risk_score < 0.6:
                risk_category = "medium_risk"
            else:
                risk_category = "high_risk"
            
            # Store in database
            feature_store = FeatureStore(
                application_id=application_id,
                debt_to_income_ratio=dti,
                credit_utilization=credit_util,
                payment_history_score=payment_history,
                employability_score=employability,
                risk_category=risk_category,
                normalized_features=features,
            )
            
            db.add(feature_store)
            db.commit()
            
            logger.info(f"Features computed and stored for application {application_id}")
            return feature_store
            
        except Exception as e:
            logger.error(f"Error computing features: {e}")
            raise

    def get_features(
        self,
        application_id: int,
        db: Session,
    ) -> Optional[FeatureStore]:
        """Get cached features for an application."""
        return db.query(FeatureStore).filter(
            FeatureStore.application_id == application_id,
            FeatureStore.is_stale == False,
        ).first()

    def mark_stale(self, application_id: int, db: Session):
        """Mark features as stale (need recomputation)."""
        feature_store = db.query(FeatureStore).filter(
            FeatureStore.application_id == application_id
        ).first()
        
        if feature_store:
            feature_store.is_stale = True
            db.commit()
            logger.info(f"Features marked stale for application {application_id}")
