from fastapi import APIRouter, Depends
from src.presentation.api.dependencies import get_redis_cache
from src.infrastructure.cache.redis_cache import RedisCache
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
async def readiness(redis: RedisCache = Depends(get_redis_cache)):
    """Readiness check including dependencies"""
    checks = {
        "api": "ok",
        "redis": "ok"
    }
    
    # Check Redis connectivity
    try:
        await redis.get("health_check")
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = "failed"
    
    status = "ready" if all(v == "ok" for v in checks.values()) else "not_ready"
    
    return {
        "status": status,
        "checks": checks
    }