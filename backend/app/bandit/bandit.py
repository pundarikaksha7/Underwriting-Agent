"""Contextual bandit implementation for model selection optimization."""

import logging
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class BanditArm:
    """Represents a model arm in the bandit."""
    name: str
    num_selections: int = 0
    num_successes: int = 0
    estimated_reward: float = 0.5
    uncertainty: float = 1.0
    alpha: float = 1.0  # For Thompson Sampling
    beta: float = 1.0   # For Thompson Sampling
    avg_cost: float = 0.0
    avg_latency: float = 0.0


class LinUCBBandit:
    """
    Linear Upper Confidence Bound (LinUCB) bandit for contextual model selection.
    
    This implements a contextual multi-armed bandit that learns which model (arm)
    performs best based on application context features.
    """

    def __init__(self, alpha: float = 0.25, exploration_rate: float = 0.1):
        """
        Initialize LinUCB bandit.
        
        Args:
            alpha: Exploration parameter (higher = more exploration)
            exploration_rate: Probability of random exploration
        """
        self.alpha = alpha
        self.exploration_rate = exploration_rate
        self.arms: Dict[str, BanditArm] = {}
        self.feature_dim = 10  # Context feature dimension
        self.V = {}  # V matrix for each arm
        self.b = {}  # b vector for each arm
        
        # Initialize for known models
        self._init_arms()

    def _init_arms(self):
        """Initialize arms for each available model."""
        models = ["gpt-4", "gpt-3.5-turbo", "gemini-pro", "local-7b"]
        
        for model in models:
            self.arms[model] = BanditArm(name=model)
            # Initialize V as identity matrix and b as zero vector
            self.V[model] = np.eye(self.feature_dim)
            self.b[model] = np.zeros(self.feature_dim)

    def select_arm(self, context: np.ndarray) -> Tuple[str, float]:
        """
        Select model arm using LinUCB.
        
        Args:
            context: Context features (complexity, confidence, debt_ratio, etc.)
        
        Returns:
            (selected_model, ucb_score)
        """
        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            arm_name = np.random.choice(list(self.arms.keys()))
            logger.info(f"Exploration: selected {arm_name}")
            return arm_name, 0.0

        ucb_scores = {}
        for arm_name, arm in self.arms.items():
            # Calculate upper confidence bound
            V_inv = np.linalg.inv(self.V[arm_name])
            theta = V_inv @ self.b[arm_name]
            
            # UCB = estimated_reward + alpha * sqrt(context' * V_inv * context)
            confidence_radius = self.alpha * np.sqrt(context @ V_inv @ context.T)
            ucb_score = (theta @ context.T) + confidence_radius
            
            ucb_scores[arm_name] = ucb_score

        selected_arm = max(ucb_scores, key=ucb_scores.get)
        ucb_score = ucb_scores[selected_arm]
        
        logger.info(f"Selected {selected_arm} with UCB score {ucb_score:.4f}")
        return selected_arm, ucb_score

    def update_arm(
        self,
        arm_name: str,
        context: np.ndarray,
        reward: float,
        cost: float = 0.0,
        latency: float = 0.0,
    ):
        """
        Update arm based on feedback.
        
        Args:
            arm_name: Name of selected arm
            context: Context features
            reward: Reward signal (0-1, where 1 = correct decision)
            cost: Cost of the decision
            latency: Latency in milliseconds
        """
        if arm_name not in self.arms:
            logger.warning(f"Unknown arm: {arm_name}")
            return

        arm = self.arms[arm_name]
        
        # Update counts
        arm.num_selections += 1
        if reward > 0.5:  # Threshold for success
            arm.num_successes += 1
        
        # Update estimated reward
        arm.estimated_reward = arm.num_successes / max(arm.num_selections, 1)
        
        # Update uncertainty (decrease as we learn)
        arm.uncertainty = 1.0 / np.sqrt(max(arm.num_selections, 1))
        
        # Update cost and latency
        arm.avg_cost = (arm.avg_cost * (arm.num_selections - 1) + cost) / arm.num_selections
        arm.avg_latency = (arm.avg_latency * (arm.num_selections - 1) + latency) / arm.num_selections
        
        # Update V and b for LinUCB
        self.V[arm_name] += context.reshape(-1, 1) @ context.reshape(1, -1)
        self.b[arm_name] += reward * context
        
        logger.info(
            f"Updated {arm_name}: reward={reward:.2f}, "
            f"success_rate={arm.estimated_reward:.2%}, "
            f"uncertainty={arm.uncertainty:.4f}"
        )

    def get_arm_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all arms."""
        stats = {}
        for arm_name, arm in self.arms.items():
            stats[arm_name] = {
                "num_selections": arm.num_selections,
                "num_successes": arm.num_successes,
                "success_rate": arm.estimated_reward,
                "uncertainty": arm.uncertainty,
                "avg_cost": arm.avg_cost,
                "avg_latency": arm.avg_latency,
            }
        return stats


class ThompsonSamplingBandit:
    """
    Thompson Sampling bandit for model selection.
    
    Simpler than LinUCB but effective for binary rewards.
    """

    def __init__(self, exploration_rate: float = 0.15):
        """
        Initialize Thompson Sampling bandit.
        
        Args:
            exploration_rate: Probability of random exploration
        """
        self.exploration_rate = exploration_rate
        self.arms: Dict[str, BanditArm] = {}
        self._init_arms()

    def _init_arms(self):
        """Initialize arms for each available model."""
        models = ["gpt-4", "gpt-3.5-turbo", "gemini-pro", "local-7b"]
        
        for model in models:
            self.arms[model] = BanditArm(
                name=model,
                alpha=1.0,  # successes + 1
                beta=1.0,   # failures + 1
            )

    def select_arm(self, context: Optional[np.ndarray] = None) -> Tuple[str, float]:
        """
        Select model arm using Thompson Sampling.
        
        Args:
            context: Optional context features (not used in basic Thompson Sampling)
        
        Returns:
            (selected_model, sampled_theta)
        """
        # Exploration vs exploitation
        if np.random.random() < self.exploration_rate:
            arm_name = np.random.choice(list(self.arms.keys()))
            logger.info(f"Exploration: selected {arm_name}")
            return arm_name, 0.0

        # Sample theta from posterior for each arm
        sampled_thetas = {}
        for arm_name, arm in self.arms.items():
            # Sample from Beta distribution
            theta = np.random.beta(arm.alpha, arm.beta)
            sampled_thetas[arm_name] = theta

        # Select arm with highest sampled theta
        selected_arm = max(sampled_thetas, key=sampled_thetas.get)
        sampled_theta = sampled_thetas[selected_arm]
        
        logger.info(f"Selected {selected_arm} with sampled theta {sampled_theta:.4f}")
        return selected_arm, sampled_theta

    def update_arm(
        self,
        arm_name: str,
        reward: float,
        cost: float = 0.0,
        latency: float = 0.0,
    ):
        """
        Update arm based on binary reward.
        
        Args:
            arm_name: Name of selected arm
            reward: 1 = success (correct decision), 0 = failure
            cost: Cost of the decision
            latency: Latency in milliseconds
        """
        if arm_name not in self.arms:
            logger.warning(f"Unknown arm: {arm_name}")
            return

        arm = self.arms[arm_name]
        
        # Update Beta distribution parameters
        if reward > 0.5:
            arm.alpha += 1  # success
        else:
            arm.beta += 1   # failure
        
        # Update counts and stats
        arm.num_selections += 1
        if reward > 0.5:
            arm.num_successes += 1
        
        arm.estimated_reward = arm.num_successes / max(arm.num_selections, 1)
        
        # Update cost and latency
        arm.avg_cost = (arm.avg_cost * (arm.num_selections - 1) + cost) / arm.num_selections
        arm.avg_latency = (arm.avg_latency * (arm.num_selections - 1) + latency) / arm.num_selections
        
        logger.info(
            f"Updated {arm_name} (Thompson): "
            f"alpha={arm.alpha}, beta={arm.beta}, "
            f"success_rate={arm.estimated_reward:.2%}"
        )

    def get_arm_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all arms."""
        stats = {}
        for arm_name, arm in self.arms.items():
            stats[arm_name] = {
                "num_selections": arm.num_selections,
                "num_successes": arm.num_successes,
                "success_rate": arm.estimated_reward,
                "alpha": arm.alpha,
                "beta": arm.beta,
                "avg_cost": arm.avg_cost,
                "avg_latency": arm.avg_latency,
            }
        return stats


class BanditManager:
    """Manager for bandit operations."""

    def __init__(self, algorithm: str = "linucb"):
        """
        Initialize bandit manager.
        
        Args:
            algorithm: "linucb" or "thompson"
        """
        self.algorithm = algorithm
        if algorithm == "linucb":
            self.bandit = LinUCBBandit(alpha=0.25)
        else:
            self.bandit = ThompsonSamplingBandit()
        
        logger.info(f"Initialized {algorithm.upper()} bandit")

    def select_model(self, context: Optional[np.ndarray] = None) -> str:
        """Select model based on current bandit state."""
        if isinstance(self.bandit, LinUCBBandit) and context is not None:
            model, _ = self.bandit.select_arm(context)
        else:
            model, _ = self.bandit.select_arm(context)
        return model

    def update(
        self,
        model: str,
        is_correct: bool,
        context: Optional[np.ndarray] = None,
        cost: float = 0.0,
        latency: float = 0.0,
    ):
        """Update bandit with feedback."""
        reward = 1.0 if is_correct else 0.0
        
        if isinstance(self.bandit, LinUCBBandit) and context is not None:
            self.bandit.update_arm(model, context, reward, cost, latency)
        else:
            self.bandit.update_arm(model, reward, cost, latency)

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get current bandit statistics."""
        return self.bandit.get_arm_stats()

    def get_best_arm(self) -> str:
        """Get best performing arm based on success rate."""
        stats = self.get_stats()
        best_arm = max(stats.items(), key=lambda x: x[1]["success_rate"])
        return best_arm[0]
