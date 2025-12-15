"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime
import psutil

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns system status and basic metrics.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        },
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check for Kubernetes.

    Returns whether the service is ready to accept traffic.
    """
    # TODO: Check model loaded, database connected, etc.
    return {"ready": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Returns whether the service is alive.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}
