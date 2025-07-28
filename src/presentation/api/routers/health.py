from fastapi import APIRouter
from src.shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"]
)


@router.get("/liveness")
async def liveness():
    """Simple liveness check"""
    return {"status": "alive"}


@router.get("/readiness")
async def readiness():
    """Readiness check - simplified without Redis"""
    return {
        "status": "ready",
        "checks": {
            "api": "ok"
        }
    }


@router.get("/")
async def health_root():
    """Health check root endpoint for compatibility"""
    return {"status": "healthy", "message": "Use /health/liveness or /health/readiness"}


@router.get("")
async def health_root_alt():
    """Alternative health check root endpoint"""
    return {"status": "healthy", "message": "Use /health/liveness or /health/readiness"}