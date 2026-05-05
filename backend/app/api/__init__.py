"""API endpoint routers."""

from .health import router as health_router
from .applications import router as applications_router
from .decisions import router as decisions_router
from .analytics import router as analytics_router

__all__ = [
    "health_router",
    "applications_router",
    "decisions_router",
    "analytics_router",
]
