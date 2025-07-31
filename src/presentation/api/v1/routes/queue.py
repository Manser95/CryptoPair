from fastapi import APIRouter, Depends
from src.presentation.api.v1.schemas.response import QueueStatusResponse
from src.presentation.api.dependencies import get_coingecko_gateway
from src.data_access.external.coingecko_gateway import CoinGeckoGateway

router = APIRouter(prefix="/queue", tags=["monitoring"])


@router.get("/status", response_model=QueueStatusResponse)
async def get_queue_status(
    gateway: CoinGeckoGateway = Depends(get_coingecko_gateway)
) -> QueueStatusResponse:
    """Get current queue and rate limit status"""
    
    stats = gateway.get_stats()
    
    return QueueStatusResponse(
        queue_size=stats["queue_size"],
        processing_rate=stats["requests_per_minute"],
        average_wait_time=stats["average_wait_time"],
        rate_limit={
            "limit": gateway.max_requests_per_minute,
            "interval": "minute",
            "current_rate": (
                stats["successful_requests"] / max(1, stats["total_requests"]) * 100
                if stats["total_requests"] > 0 else 0
            )
        },
        circuit_breaker=stats["circuit_breaker_state"]
    )


@router.get("/stats")
async def get_detailed_stats(
    gateway: CoinGeckoGateway = Depends(get_coingecko_gateway)
) -> dict:
    """Get detailed gateway statistics including request history"""
    stats = gateway.get_stats()
    
    # Add warning if approaching rate limit
    if stats["requests_last_minute"] >= gateway.max_requests_per_minute * 0.8:
        stats["warning"] = f"⚠️ Approaching rate limit! {stats['requests_last_minute']}/{gateway.max_requests_per_minute} requests in last minute"
    
    return stats