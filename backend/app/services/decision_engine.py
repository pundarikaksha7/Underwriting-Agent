"""Decision engine orchestrator for underwriting decisions."""

import logging
import time
import numpy as np
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models.db import Application, Decision, DecisionHistory, BanditArm, RouterLog
from app.models.schemas import DecisionResponse, UnderwritingResponse
from app.services.llm_service import LLMService
from app.services.ml_service import MLModelService
from app.router.llm_router import LLMRouter, RoutingStrategy
from app.bandit.bandit import BanditManager
from app.utils.feature_store import FeatureStoreService
from app.utils.rag_service import RAGService

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Main decision engine for underwriting."""

    def __init__(self):
        """Initialize decision engine with all components."""
        self.llm_service = LLMService()
        self.ml_service = MLModelService()
        self.router = LLMRouter()
        self.bandit = BanditManager(algorithm=settings.bandit_algorithm)
        self.feature_store = FeatureStoreService()
        self.rag_service = RAGService() if settings.enable_rag else None
        
        # Set router strategy
        strategy_map = {
            "cost": RoutingStrategy.COST_OPTIMIZED,
            "latency": RoutingStrategy.LATENCY_OPTIMIZED,
            "accuracy": RoutingStrategy.ACCURACY_OPTIMIZED,
            "balanced": RoutingStrategy.BALANCED,
        }
        strategy = strategy_map.get("balanced", RoutingStrategy.BALANCED)
        self.router.set_strategy(strategy)

    async def make_decision(
        self,
        application_data: Dict[str, Any],
        db: Session,
        application_id: Optional[int] = None,
        force_model: Optional[str] = None,
        include_rag: bool = False,
    ) -> Tuple[DecisionResponse, Dict[str, Any]]:
        """
        Make underwriting decision.
        
        Returns:
            (DecisionResponse, decision_metadata)
        """
        start_time = time.time()
        decision_id = None
        
        try:
            # Step 1: Extract features
            logger.info(f"Processing application decision")
            feature_array, extracted_features = self.ml_service.extract_features(application_data)
            
            # Calculate input complexity
            input_complexity = self._calculate_complexity(extracted_features)
            
            # Step 2: ML model prediction
            ml_decision, ml_confidence, ml_metadata = self.ml_service.predict(application_data)
            logger.info(f"ML model decision: {ml_decision} (confidence: {ml_confidence:.2f})")
            
            # Step 3: Route to determine which models to use
            context = feature_array[0] if feature_array.size > 0 else None
            
            if force_model:
                selected_model = force_model
                use_rag = include_rag
                routing_rationale = f"Forced model: {force_model}"
            else:
                routing_decision = self.router.route(
                    ml_confidence=ml_confidence,
                    input_complexity=input_complexity,
                    ml_features=extracted_features,
                )
                selected_model = routing_decision.selected_model
                use_rag = routing_decision.use_rag
                routing_rationale = routing_decision.rationale
            
            logger.info(f"Routing decision: {selected_model}, RAG={use_rag}")
            
            # Step 4: Get LLM reasoning if needed
            reasoning_text = ""
            llm_tokens = 0
            llm_latency = 0
            
            if selected_model != "ml-only":
                try:
                    reasoning_text, llm_metadata = await self.llm_service.generate_reasoning(
                        application_data,
                        model=selected_model,
                        include_metrics=True,
                    )
                    llm_tokens = llm_metadata.get("tokens_used", 0)
                    llm_latency = llm_metadata.get("latency_ms", 0)
                    logger.info(f"LLM reasoning generated: {llm_tokens} tokens, {llm_latency:.2f}ms")
                except Exception as e:
                    logger.error(f"LLM reasoning failed: {e}, using ML only")
                    selected_model = "ml-only"
                    reasoning_text = f"LLM unavailable; using ML decision"
            
            # Step 5: RAG retrieval if needed
            rag_context = ""
            if use_rag and self.rag_service:
                try:
                    rag_results = await self.rag_service.retrieve(
                        query=f"{application_data.get('loan_purpose')} {ml_decision}",
                        top_k=3,
                    )
                    rag_context = "\n".join([r.get("content", "") for r in rag_results])
                    reasoning_text += f"\n\nRegulatory Context: {rag_context}"
                except Exception as e:
                    logger.warning(f"RAG retrieval failed: {e}")
            
            # Step 6: Combine signals and refine decision
            final_decision, confidence, risk_score, approval_amount, interest_rate = \
                self._combine_signals(ml_decision, ml_confidence, reasoning_text, application_data)
            
            # Step 7: Calculate metrics
            total_latency = (time.time() - start_time) * 1000
            total_tokens = llm_tokens
            estimated_cost = self._estimate_total_cost(selected_model, total_tokens)
            
            # Save decision to database
            if application_id and db:
                decision = Decision(
                    application_id=application_id,
                    user_id=None,  # Would be set in API layer
                    decision=final_decision,
                    confidence=confidence,
                    risk_score=risk_score,
                    primary_model_used=selected_model,
                    reasoning=reasoning_text[:2000],  # Truncate for DB
                    explanation=self._generate_explanation(
                        final_decision, 
                        confidence, 
                        extracted_features, 
                        reasoning_text
                    ),
                    routing_decision={
                        "selected_model": selected_model,
                        "use_rag": use_rag,
                        "rationale": routing_rationale,
                        "ml_confidence": ml_confidence,
                        "complexity": input_complexity,
                    },
                    rag_used=use_rag,
                    latency_ms=total_latency,
                    total_tokens_used=total_tokens,
                    estimated_cost=estimated_cost,
                    decision_details={
                        "ml_decision": ml_decision,
                        "ml_confidence": ml_confidence,
                        "risk_score": risk_score,
                    },
                    approved_amount=approval_amount,
                    offered_interest_rate=interest_rate,
                )
                db.add(decision)
                db.commit()
                decision_id = decision.id
                logger.info(f"Decision saved to DB: {decision_id}")
            
            # Build response
            response = UnderwritingResponse(
                decision_id=decision_id or 0,
                application_id=application_id or 0,
                decision=final_decision,
                confidence=confidence,
                risk_score=risk_score,
                approved_amount=approval_amount,
                offered_interest_rate=interest_rate,
                reasoning=reasoning_text[:1000],
                explanation=self._generate_explanation(
                    final_decision, 
                    confidence, 
                    extracted_features,
                    reasoning_text
                ),
                model_used=selected_model,
                latency_ms=total_latency,
                total_tokens_used=total_tokens,
                estimated_cost=estimated_cost,
                rag_used=use_rag,
                routing_details={
                    "selected_model": selected_model,
                    "ml_confidence": ml_confidence,
                    "input_complexity": input_complexity,
                    "rag_enabled": use_rag,
                },
            )
            
            metadata = {
                "ml_features": extracted_features,
                "ml_decision": ml_decision,
                "ml_confidence": ml_confidence,
                "llm_tokens": llm_tokens,
                "rag_used": use_rag,
                "routing_rationale": routing_rationale,
            }
            
            return response, metadata
            
        except Exception as e:
            logger.error(f"Decision engine error: {e}", exc_info=True)
            # Return error response
            response = UnderwritingResponse(
                decision_id=decision_id or 0,
                application_id=application_id or 0,
                decision="pending",
                confidence=0.0,
                risk_score=0.5,
                reasoning=f"Error: {str(e)}",
                explanation=f"Decision engine encountered an error: {str(e)}",
                model_used="error",
                latency_ms=(time.time() - start_time) * 1000,
                total_tokens_used=0,
                estimated_cost=0.0,
                rag_used=False,
            )
            return response, {"error": str(e)}

    def record_feedback(
        self,
        decision_id: int,
        is_correct: bool,
        db: Session,
        context: Optional[np.ndarray] = None,
    ):
        """
        Record feedback on a decision for learning.
        
        Args:
            decision_id: ID of the decision
            is_correct: Whether the decision was correct
            db: Database session
            context: Optional context features for bandit update
        """
        try:
            decision = db.query(Decision).filter(Decision.id == decision_id).first()
            if not decision:
                logger.warning(f"Decision {decision_id} not found")
                return
            
            # Update decision with feedback
            decision.feedback = "correct" if is_correct else "incorrect"
            decision.feedback_provided_at = datetime.utcnow()
            
            # Update bandit with feedback
            model = decision.primary_model_used
            cost = decision.estimated_cost
            latency = decision.latency_ms
            
            self.bandit.update(
                model=model,
                is_correct=is_correct,
                context=context,
                cost=cost,
                latency=latency,
            )
            
            # Optional: retrain ML model periodically
            # This would be done in a background job
            
            db.commit()
            logger.info(f"Feedback recorded for decision {decision_id}: {is_correct}")
            
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")

    @staticmethod
    def _calculate_complexity(features: Dict[str, float]) -> float:
        """Calculate input complexity score (0-1)."""
        # Complex if: high DTI, low credit score, employment issues, etc.
        complexity = 0.5
        
        dti = features.get('debt_to_income', 0.5)
        if dti > 0.5:
            complexity += 0.2
        
        credit = features.get('credit_score_normalized', 0.5)
        if credit < 0.5:
            complexity += 0.15
        
        employment = features.get('employment_stability', 0.3)
        if employment < 0.3:
            complexity += 0.15
        
        return min(complexity, 1.0)

    @staticmethod
    def _combine_signals(
        ml_decision: str,
        ml_confidence: float,
        reasoning_text: str,
        application_data: Dict[str, Any],
    ) -> Tuple[str, float, float, Optional[float], Optional[float]]:
        """
        Combine ML and LLM signals into final decision.
        
        Returns:
            (final_decision, confidence, risk_score, approved_amount, interest_rate)
        """
        # For now, trust ML model but adjust based on LLM reasoning
        final_decision = ml_decision
        confidence = ml_confidence
        
        # Adjust confidence if LLM reasoning is available
        if reasoning_text and len(reasoning_text) > 50:
            confidence = min(confidence * 1.1, 1.0)  # Slight boost if LLM provided reasoning
        
        # Calculate risk score (inverse of confidence)
        risk_score = 1.0 - confidence
        
        # Calculate approved amount if approved
        approved_amount = None
        interest_rate = None
        
        if final_decision == "approved":
            requested_amount = application_data.get('loan_amount', 0)
            # Approve 80-100% based on confidence
            approval_percentage = 0.8 + (confidence * 0.2)
            approved_amount = requested_amount * approval_percentage
            
            # Interest rate based on risk
            base_rate = 0.05  # 5%
            risk_adjustment = risk_score * 0.10  # Up to 10% risk premium
            interest_rate = base_rate + risk_adjustment
        
        return final_decision, confidence, risk_score, approved_amount, interest_rate

    @staticmethod
    def _generate_explanation(
        decision: str,
        confidence: float,
        features: Dict[str, float],
        reasoning: str,
    ) -> str:
        """Generate human-readable explanation of the decision."""
        parts = []
        
        # Decision statement
        if decision == "approved":
            parts.append(f"Application APPROVED with {confidence*100:.0f}% confidence.")
        elif decision == "rejected":
            parts.append(f"Application REJECTED. Risk factors outweigh qualifications.")
        else:
            parts.append(f"Application marked as {decision.upper()} pending further review.")
        
        # Key factors
        parts.append("\nKey Decision Factors:")
        
        dti = features.get('debt_to_income', 0.5)
        if dti > 0.5:
            parts.append(f"- High debt-to-income ratio ({dti:.2f}) is a concern")
        else:
            parts.append(f"- Healthy debt-to-income ratio ({dti:.2f})")
        
        credit = features.get('credit_score_normalized', 0.5)
        if credit > 0.7:
            parts.append(f"- Strong credit history")
        elif credit < 0.4:
            parts.append(f"- Weak credit history requires careful consideration")
        
        employment = features.get('employment_stability', 0.3)
        if employment > 0.6:
            parts.append(f"- Stable employment history")
        else:
            parts.append(f"- Employment stability is a limiting factor")
        
        # LLM reasoning snippet if available
        if reasoning:
            summary = reasoning.split('\n')[0][:200]
            parts.append(f"\nAnalysis Summary: {summary}")
        
        # Risk summary
        risk_score = 1.0 - confidence
        if risk_score < 0.3:
            risk_level = "Low Risk"
        elif risk_score < 0.6:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        
        parts.append(f"\nRisk Profile: {risk_level}")
        
        return "\n".join(parts)

    @staticmethod
    def _estimate_total_cost(model: str, tokens: int) -> float:
        """Estimate total cost of decision."""
        pricing = {
            "gpt-4": 0.03 / 1000,
            "gpt-3.5-turbo": 0.0005 / 1000,
            "gemini-pro": 0.0005 / 1000,
            "local-7b": 0.0,
            "ml-only": 0.0,
        }
        
        rate = pricing.get(model, 0.001 / 1000)
        return tokens * rate
