from typing import Optional
from src.data_access.repositories.price_repository import PriceRepository
from src.data_access.repositories.redis_cache_repository import RedisCacheRepository
from src.data_access.external.coingecko_gateway import CoinGeckoGateway
from src.services.price_service import PriceService
from src.services.cache_service import CacheService
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)

# Singleton instances
_gateway: Optional[CoinGeckoGateway] = None
_price_repository: Optional[PriceRepository] = None
_cache_repository: Optional[RedisCacheRepository] = None
_cache_service: Optional[CacheService] = None
_price_service: Optional[PriceService] = None


async def get_coingecko_gateway() -> CoinGeckoGateway:
    """Get CoinGecko gateway singleton"""
    global _gateway
    if _gateway is None:
        _gateway = CoinGeckoGateway()
        await _gateway.start()
    return _gateway


async def get_cache_repository() -> RedisCacheRepository:
    """Get cache repository"""
    global _cache_repository
    if _cache_repository is None:
        _cache_repository = RedisCacheRepository(
            default_ttl=settings.cache_ttl
        )
        await _cache_repository.start()
    return _cache_repository


async def get_price_repository() -> PriceRepository:
    """Get price repository"""
    global _price_repository
    if _price_repository is None:
        gateway = await get_coingecko_gateway()
        # Pass the gateway to the repository
        _price_repository = PriceRepository(gateway)
    return _price_repository


async def get_cache_service() -> CacheService:
    """Get cache service"""
    global _cache_service
    if _cache_service is None:
        cache_repo = await get_cache_repository()
        _cache_service = CacheService(cache_repo)
    return _cache_service


async def get_price_service() -> PriceService:
    """Get price service"""
    global _price_service
    if _price_service is None:
        price_repo = await get_price_repository()
        cache_repo = await get_cache_repository()
        gateway = await get_coingecko_gateway()
        _price_service = PriceService(price_repo, cache_repo, gateway)
    return _price_service


async def startup_event():
    """Initialize services on startup"""
    # Start gateway
    gateway = await get_coingecko_gateway()
    
    # Initialize cache
    cache_repo = await get_cache_repository()
    
    # Initialize price service
    price_service = await get_price_service()
    
    # Skip preloading to avoid rate limits at startup
    # Pairs will be cached on first request
    
    logger.info("Services initialized successfully")


async def shutdown_event():
    """Cleanup on shutdown"""
    # Stop gateway
    if _gateway:
        await _gateway.stop()
        await _gateway.close()
    
    # Stop cache cleanup
    if _cache_repository:
        await _cache_repository.stop()
    
    logger.info("All services shut down successfully")