"""Health check endpoints."""

from fastapi import APIRouter
from datetime import datetime
import psutil
import httpx
from typing import Dict, Any

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
    Validates critical external dependencies and system resources.
    """
    checks: Dict[str, Any] = {}
    all_ready = True

    # Check USGS API connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("https://earthquake.usgs.gov/fdsnws/event/1/version")
            checks["usgs_api"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "available": response.status_code == 200,
            }
            if response.status_code != 200:
                all_ready = False
    except Exception as e:
        checks["usgs_api"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
        }
        all_ready = False

    # Check system resources
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage("/").percent

    checks["system_resources"] = {
        "memory_available": memory_percent < 90,
        "disk_available": disk_percent < 90,
        "memory_percent": memory_percent,
        "disk_percent": disk_percent,
    }

    if memory_percent >= 90 or disk_percent >= 90:
        all_ready = False

    # Check if H3 grid can be initialized
    try:
        from hazard.common.geo import H3Grid
        grid = H3Grid(resolution=4)
        checks["h3_grid"] = {
            "status": "healthy",
            "available": True,
        }
    except Exception as e:
        checks["h3_grid"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
        }
        all_ready = False

    return {
        "ready": all_ready,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check for Kubernetes.

    Returns whether the service is alive.
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}
