"""Application configuration and settings."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuration settings for the Decision Intelligence Platform."""

    # App
    app_name: str = "Underwriting Agent"
    debug: bool = False
    version: str = "1.0.0"

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/underwriting"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # LLM Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_model_fast: str = "gpt-3.5-turbo"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"

    # LLM Router Config
    enable_router: bool = True
    router_cost_optimization: bool = True
    router_latency_optimization: bool = True
    default_model_threshold: float = 0.7  # confidence threshold
    use_rag_threshold: float = 0.6

    # Feature Store
    feature_store_type: str = "postgres"  # postgres or redis

    # RAG Configuration
    enable_rag: bool = True
    vector_db_type: str = "faiss"  # faiss or pinecone
    rag_reranker_enabled: bool = True
    rag_top_k: int = 5

    # Bandit Configuration
    bandit_algorithm: str = "linucb"  # linucb or thompson
    bandit_exploration_rate: float = 0.1
    bandit_update_frequency: int = 100  # update after N decisions

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4

    # JWT/Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or standard

    # Decision Engine
    ml_model_type: str = "lightgbm"  # lightgbm or sklearn
    decision_confidence_threshold: float = 0.5
    use_llm_reasoning: bool = True

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60

    # Simulation
    simulation_mode: bool = False
    simulation_data_size: int = 1000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
