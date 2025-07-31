from fastapi import APIRouter, Depends
from datetime import datetime
from src.presentation.api.v1.schemas.response import HealthResponse
from src.presentation.api.dependencies import (
    get_price_service, get_cache_service, get_coingecko_gateway
)
from src.services.price_service import PriceService
from src.services.cache_service import CacheService
from src.data_access.external.coingecko_gateway import CoinGeckoGateway
from src.shared.circuit_breaker.breaker import CircuitState

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check(
    price_service: PriceService = Depends(get_price_service),
    cache_service: CacheService = Depends(get_cache_service),
    gateway: CoinGeckoGateway = Depends(get_coingecko_gateway)
) -> HealthResponse:
    """Check health status of the API and its dependencies"""
    
    # Check services
    services = {
        "api": "healthy",
        "cache": "healthy",
        "coingecko_gateway": "healthy",
        "circuit_breaker": gateway.circuit_breaker.state
    }
    
    # Check if gateway is running
    if not gateway._running:
        services["coingecko_gateway"] = "not_started"
    
    # Overall status
    overall_status = "healthy"
    if any(v != "healthy" and v != "closed" for v in services.values()):
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        version="v1",
        timestamp=datetime.utcnow(),
        services=services
    )


@router.get("/ready")
async def readiness_check(
    gateway: CoinGeckoGateway = Depends(get_coingecko_gateway)
) -> dict:
    """Check if the service is ready to handle requests"""
    
    is_ready = gateway._running and gateway.circuit_breaker.state != "open"
    
    return {
        "ready": is_ready,
        "gateway_running": gateway._running,
        "circuit_breaker": gateway.circuit_breaker.state
    }


@router.get("/live")
async def liveness_check() -> dict:
    """Simple liveness check"""
    return {"status": "alive"}


@router.post("/circuit-breaker/reset")
async def reset_circuit_breaker(
    gateway: CoinGeckoGateway = Depends(get_coingecko_gateway)
) -> dict:
    """Reset circuit breaker to closed state"""
    
    # Get current state before reset
    current_state = gateway.circuit_breaker.state
    stats = gateway.circuit_breaker.get_stats()
    
    if current_state == CircuitState.OPEN:
        # Reset the circuit breaker
        gateway.circuit_breaker._state = CircuitState.CLOSED
        gateway.circuit_breaker._failure_count = 0
        gateway.circuit_breaker._update_metrics()
        
        return {
            "message": "Circuit breaker reset successfully",
            "previous_state": current_state.value,
            "current_state": gateway.circuit_breaker.state.value,
            "stats": stats
        }
    else:
        return {
            "message": "Circuit breaker is already in a healthy state",
            "current_state": current_state.value,
            "stats": stats
        }