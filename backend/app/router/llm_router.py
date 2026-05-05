"""LLM Router service for dynamic model selection."""

import logging
import time
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RoutingDecision:
    """Result of routing decision."""
    selected_model: str
    use_rag: bool
    confidence_threshold: float
    rationale: str
    alternative_models: List[str]
    estimated_cost: float
    estimated_latency: float


class RoutingStrategy(str, Enum):
    """Different routing strategies."""
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"
    ACCURACY_OPTIMIZED = "accuracy_optimized"
    BALANCED = "balanced"


class LLMRouter:
    """Dynamic router for LLM model selection."""

    # Model profiles: (cost_per_1k_tokens, avg_latency_ms, accuracy_score)
    MODEL_PROFILES = {
        "gpt-4": {
            "cost": 0.03,
            "latency": 3000,
            "accuracy": 0.95,
            "max_tokens": 8192,
            "category": "expensive",
        },
        "gpt-3.5-turbo": {
            "cost": 0.0005,
            "latency": 800,
            "accuracy": 0.85,
            "max_tokens": 4096,
            "category": "cheap",
        },
        "gemini-pro": {
            "cost": 0.0005,
            "latency": 2000,
            "accuracy": 0.88,
            "max_tokens": 32768,
            "category": "cheap",
        },
        "local-7b": {
            "cost": 0.0,
            "latency": 1500,
            "accuracy": 0.75,
            "max_tokens": 2048,
            "category": "free",
        },
    }

    def __init__(self):
        """Initialize router."""
        self.strategy: RoutingStrategy = RoutingStrategy.BALANCED
        self.cost_budget: float = 0.50  # Default $0.50 per decision
        self.latency_budget: float = 5000  # Default 5 seconds
        self.min_confidence_threshold: float = settings.default_model_threshold

    def set_strategy(self, strategy: RoutingStrategy):
        """Set routing strategy."""
        self.strategy = strategy
        logger.info(f"Router strategy set to: {strategy}")

    def route(
        self,
        ml_confidence: float,
        input_complexity: float,
        user_constraints: Optional[Dict[str, Any]] = None,
        ml_features: Optional[Dict[str, float]] = None,
    ) -> RoutingDecision:
        """
        Determine which model to use and whether to use RAG.
        
        Args:
            ml_confidence: Confidence from ML model (0-1)
            input_complexity: Complexity score of input (0-1)
            user_constraints: Optional budget/latency constraints
            ml_features: Optional ML features for contextual routing
        
        Returns:
            RoutingDecision with selected model and configuration
        """
        logger.info(
            f"Routing decision: ML confidence={ml_confidence:.2f}, "
            f"complexity={input_complexity:.2f}"
        )

        # Apply user constraints if provided
        cost_budget = self.cost_budget
        latency_budget = self.latency_budget
        
        if user_constraints:
            cost_budget = user_constraints.get("cost_budget", cost_budget)
            latency_budget = user_constraints.get("latency_budget", latency_budget)

        # Determine if we need LLM reasoning
        needs_llm = self._determine_llm_necessity(ml_confidence, input_complexity)

        if not needs_llm:
            # ML model is confident enough, don't use LLM
            return RoutingDecision(
                selected_model="ml-only",
                use_rag=False,
                confidence_threshold=self.min_confidence_threshold,
                rationale="ML model confidence sufficient; LLM reasoning skipped",
                alternative_models=["gpt-3.5-turbo", "local-7b"],
                estimated_cost=0.0,
                estimated_latency=100,  # Just ML inference
            )

        # Select best model based on strategy and constraints
        selected_model = self._select_model(
            cost_budget=cost_budget,
            latency_budget=latency_budget,
            complexity=input_complexity,
            strategy=self.strategy,
        )

        # Determine if RAG is needed
        use_rag = self._determine_rag_usage(
            ml_confidence=ml_confidence,
            complexity=input_complexity,
            model=selected_model,
        )

        # Get model profile
        profile = self.MODEL_PROFILES.get(selected_model, {})
        estimated_cost = profile.get("cost", 0.001) * (input_complexity * 500)  # Rough estimate
        estimated_latency = profile.get("latency", 1000) + (100 if use_rag else 0)

        rationale = self._generate_routing_rationale(
            selected_model=selected_model,
            use_rag=use_rag,
            ml_confidence=ml_confidence,
            complexity=input_complexity,
            strategy=self.strategy,
        )

        # Alternative models
        alternative_models = [m for m in self.MODEL_PROFILES.keys() if m != selected_model][:2]

        return RoutingDecision(
            selected_model=selected_model,
            use_rag=use_rag,
            confidence_threshold=self._get_confidence_threshold(selected_model),
            rationale=rationale,
            alternative_models=alternative_models,
            estimated_cost=estimated_cost,
            estimated_latency=estimated_latency,
        )

    def _determine_llm_necessity(self, ml_confidence: float, complexity: float) -> bool:
        """
        Determine if LLM reasoning is needed.
        
        Skip LLM if ML model is very confident and input is simple.
        """
        # If ML is very confident and input is simple, we don't need LLM
        if ml_confidence > 0.85 and complexity < 0.3:
            logger.info("LLM reasoning not required (high confidence + low complexity)")
            return False

        # If input is complex or confidence is low, we need LLM reasoning
        if complexity > 0.7 or ml_confidence < 0.5:
            logger.info("LLM reasoning required (low confidence or high complexity)")
            return True

        # Default: use LLM for edge cases
        return True

    def _select_model(
        self,
        cost_budget: float,
        latency_budget: float,
        complexity: float,
        strategy: RoutingStrategy,
    ) -> str:
        """Select best model based on constraints and strategy."""
        
        # Filter available models
        available_models = self._filter_by_constraints(cost_budget, latency_budget)
        
        if not available_models:
            # Fallback to cheapest
            available_models = ["gpt-3.5-turbo", "local-7b"]

        # Score models based on strategy
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            selected = min(available_models, key=lambda m: self.MODEL_PROFILES[m]["cost"])
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            selected = min(available_models, key=lambda m: self.MODEL_PROFILES[m]["latency"])
        elif strategy == RoutingStrategy.ACCURACY_OPTIMIZED:
            selected = max(available_models, key=lambda m: self.MODEL_PROFILES[m]["accuracy"])
        else:  # BALANCED
            # Score combining all factors
            scores = {}
            for model in available_models:
                profile = self.MODEL_PROFILES[model]
                # Normalize scores to 0-1
                cost_score = 1 - min(profile["cost"] / 0.05, 1)  # Normalize to max $0.05
                latency_score = 1 - min(profile["latency"] / 3000, 1)  # Normalize to 3s
                accuracy_score = profile["accuracy"]
                
                # Weighted combination
                scores[model] = (cost_score * 0.3) + (latency_score * 0.3) + (accuracy_score * 0.4)
            
            selected = max(scores, key=scores.get)

        logger.info(f"Selected model: {selected} (strategy: {strategy})")
        return selected

    def _filter_by_constraints(self, cost_budget: float, latency_budget: float) -> List[str]:
        """Filter models by cost and latency constraints."""
        viable = []
        for model, profile in self.MODEL_PROFILES.items():
            if profile["cost"] <= cost_budget and profile["latency"] <= latency_budget:
                viable.append(model)
        
        return viable if viable else list(self.MODEL_PROFILES.keys())

    def _determine_rag_usage(
        self,
        ml_confidence: float,
        complexity: float,
        model: str,
    ) -> bool:
        """
        Determine if RAG should be used.
        
        Use RAG if confidence is low or if complexity is high.
        """
        if not settings.enable_rag:
            return False

        # Use RAG for edge cases
        if ml_confidence < settings.use_rag_threshold or complexity > 0.7:
            logger.info(f"RAG will be used (confidence={ml_confidence:.2f}, complexity={complexity:.2f})")
            return True

        return False

    @staticmethod
    def _get_confidence_threshold(model: str) -> float:
        """Get confidence threshold for decision to use a model."""
        thresholds = {
            "gpt-4": 0.3,  # More conservative for expensive model
            "gpt-3.5-turbo": 0.5,
            "gemini-pro": 0.5,
            "local-7b": 0.6,  # Less conservative for free model
            "ml-only": 0.85,
        }
        return thresholds.get(model, 0.5)

    @staticmethod
    def _generate_routing_rationale(
        selected_model: str,
        use_rag: bool,
        ml_confidence: float,
        complexity: float,
        strategy: RoutingStrategy,
    ) -> str:
        """Generate human-readable explanation of routing decision."""
        parts = []
        
        parts.append(f"Model selected: {selected_model}")
        parts.append(f"Strategy: {strategy}")
        
        if use_rag:
            parts.append("Retrieval-Augmented Generation enabled for contextual support")
        
        if ml_confidence < 0.5:
            parts.append(f"ML model confidence low ({ml_confidence:.2f}); LLM reasoning needed for support")
        elif ml_confidence > 0.8:
            parts.append(f"ML model confidence high ({ml_confidence:.2f}); LLM used for explainability")
        
        if complexity > 0.7:
            parts.append(f"Application complexity high ({complexity:.2f}); detailed LLM analysis required")
        
        return "; ".join(parts)
