"""Health check endpoint."""

from fastapi import APIRouter, status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "component": "underwriting-agent",
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check endpoint."""
    return {
        "ready": True,
        "message": "Service is ready to accept requests",
    }
