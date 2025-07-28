from src.infrastructure.api_clients.coingecko_client import CoinGeckoClient
from src.infrastructure.repositories.price_repository import PriceRepository
from src.infrastructure.cache.memory_cache import MemoryCache
from src.infrastructure.cache.redis_cache import RedisCache
from src.infrastructure.services.cache_service import MultiLevelCacheService
from src.application.use_cases.get_price import GetPriceUseCase

# Singleton instances
_coingecko_client = None
_memory_cache = None
_redis_cache = None
_cache_service = None
_price_repository = None


async def get_coingecko_client() -> CoinGeckoClient:
    global _coingecko_client
    if _coingecko_client is None:
        _coingecko_client = CoinGeckoClient()
    return _coingecko_client


async def get_memory_cache() -> MemoryCache:
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache


async def get_redis_cache() -> RedisCache:
    global _redis_cache
    if _redis_cache is None:
        _redis_cache = RedisCache()
    return _redis_cache


async def get_cache_service() -> MultiLevelCacheService:
    global _cache_service
    if _cache_service is None:
        memory_cache = await get_memory_cache()
        redis_cache = await get_redis_cache()
        _cache_service = MultiLevelCacheService(memory_cache, redis_cache)
    return _cache_service


async def get_price_repository() -> PriceRepository:
    global _price_repository
    if _price_repository is None:
        client = await get_coingecko_client()
        _price_repository = PriceRepository(client)
    return _price_repository


async def get_price_use_case() -> GetPriceUseCase:
    repository = await get_price_repository()
    cache_service = await get_cache_service()
    return GetPriceUseCase(repository, cache_service)