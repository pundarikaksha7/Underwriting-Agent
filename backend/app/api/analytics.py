"""Analytics and monitoring endpoints."""

import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.models.db import Decision, BanditArm, RouterLog
from app.models.schemas import ModelMetricsResponse, RoutingAnalytics, BanditMetrics
from app.services.decision_engine import decision_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/routing", response_model=RoutingAnalytics)
async def get_routing_analytics(
    db: Session = Depends(get_db),
):
    """Get analytics on routing decisions."""
    try:
        # Get decision statistics
        total_decisions = db.query(Decision).count()
        
        # Model distribution
        model_dist = db.query(
            Decision.primary_model_used,
            func.count(Decision.id)
        ).group_by(Decision.primary_model_used).all()
        
        model_distribution = {model: count for model, count in model_dist}
        
        # Average latency by model
        latency_data = db.query(
            Decision.primary_model_used,
            func.avg(Decision.latency_ms)
        ).group_by(Decision.primary_model_used).all()
        
        avg_latency_by_model = {model: latency for model, latency in latency_data}
        
        # Average cost by model
        cost_data = db.query(
            Decision.primary_model_used,
            func.avg(Decision.estimated_cost)
        ).group_by(Decision.primary_model_used).all()
        
        avg_cost_by_model = {model: cost for model, cost in cost_data}
        
        # Decision distribution
        decision_dist = db.query(
            Decision.decision,
            func.count(Decision.id)
        ).group_by(Decision.decision).all()
        
        decision_distribution = {dec: count for dec, count in decision_dist}
        
        # Average confidence
        avg_confidence = db.query(func.avg(Decision.confidence)).scalar() or 0.0
        
        return RoutingAnalytics(
            total_decisions=total_decisions,
            model_distribution=model_distribution,
            avg_latency_by_model=avg_latency_by_model,
            avg_cost_by_model=avg_cost_by_model,
            decision_distribution=decision_distribution,
            avg_confidence=avg_confidence,
        )
        
    except Exception as e:
        logger.error(f"Error fetching routing analytics: {e}")
        return RoutingAnalytics(
            total_decisions=0,
            model_distribution={},
            avg_latency_by_model={},
            avg_cost_by_model={},
            decision_distribution={},
            avg_confidence=0.0,
        )


@router.get("/bandit", response_model=Dict[str, BanditMetrics])
async def get_bandit_metrics():
    """Get contextual bandit metrics for all arms."""
    try:
        stats = decision_engine.bandit.get_stats()
        
        result = {}
        for model_name, stat in stats.items():
            result[model_name] = BanditMetrics(
                model_name=model_name,
                num_selections=stat["num_selections"],
                num_successes=stat["num_successes"],
                estimated_reward=stat["success_rate"],
                uncertainty=stat["uncertainty"],
                avg_cost=stat["avg_cost"],
                avg_latency=stat["avg_latency"],
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching bandit metrics: {e}")
        return {}


@router.get("/performance", response_model=Dict[str, Any])
async def get_system_performance(
    db: Session = Depends(get_db),
):
    """Get overall system performance metrics."""
    try:
        total_decisions = db.query(Decision).count()
        
        # Approved vs rejected
        approved = db.query(Decision).filter(Decision.decision == "approved").count()
        rejected = db.query(Decision).filter(Decision.decision == "rejected").count()
        conditional = db.query(Decision).filter(Decision.decision == "conditional").count()
        
        # Decision accuracy (from feedback)
        correct_decisions = db.query(Decision).filter(Decision.feedback == "correct").count()
        incorrect_decisions = db.query(Decision).filter(Decision.feedback == "incorrect").count()
        
        accuracy = None
        if correct_decisions + incorrect_decisions > 0:
            accuracy = correct_decisions / (correct_decisions + incorrect_decisions)
        
        # Latency and cost metrics
        avg_latency = db.query(func.avg(Decision.latency_ms)).scalar() or 0
        avg_cost = db.query(func.avg(Decision.estimated_cost)).scalar() or 0
        total_cost = db.query(func.sum(Decision.estimated_cost)).scalar() or 0
        
        # Token usage
        total_tokens = db.query(func.sum(Decision.total_tokens_used)).scalar() or 0
        
        return {
            "total_decisions": total_decisions,
            "approved_count": approved,
            "rejected_count": rejected,
            "conditional_count": conditional,
            "approval_rate": (approved / total_decisions * 100) if total_decisions > 0 else 0,
            "accuracy": accuracy,
            "correct_decisions": correct_decisions,
            "incorrect_decisions": incorrect_decisions,
            "avg_latency_ms": avg_latency,
            "avg_cost_usd": avg_cost,
            "total_cost_usd": total_cost,
            "total_tokens_used": total_tokens,
        }
        
    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}")
        return {
            "error": str(e),
            "total_decisions": 0,
        }


@router.get("/model-comparison", response_model=Dict[str, Dict[str, Any]])
async def compare_models(
    db: Session = Depends(get_db),
):
    """Compare performance across different models."""
    try:
        model_stats = {}
        
        models = db.query(Decision.primary_model_used).distinct().all()
        
        for (model,) in models:
            decisions = db.query(Decision).filter(
                Decision.primary_model_used == model
            ).all()
            
            if not decisions:
                continue
            
            count = len(decisions)
            approved = len([d for d in decisions if d.decision == "approved"])
            
            # Accuracy from feedback
            correct = len([d for d in decisions if d.feedback == "correct"])
            incorrect = len([d for d in decisions if d.feedback == "incorrect"])
            accuracy = correct / (correct + incorrect) if (correct + incorrect) > 0 else None
            
            # Latency and cost
            latencies = [d.latency_ms for d in decisions if d.latency_ms]
            costs = [d.estimated_cost for d in decisions if d.estimated_cost]
            
            model_stats[model] = {
                "count": count,
                "approved": approved,
                "approval_rate": (approved / count * 100) if count > 0 else 0,
                "accuracy": accuracy,
                "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
                "avg_cost_usd": sum(costs) / len(costs) if costs else 0,
                "avg_confidence": sum(d.confidence for d in decisions) / count if count > 0 else 0,
            }
        
        return model_stats
        
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        return {}
