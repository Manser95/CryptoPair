from src.infrastructure.api_clients.coingecko_client import CoinGeckoClient
from src.infrastructure.repositories.price_repository import PriceRepository
from src.infrastructure.services.cache_service import CacheService
from src.infrastructure.cache.optimized_memory_cache import OptimizedMemoryCache
from src.infrastructure.cache.warming_cache import CacheWarmer
from src.application.use_cases.get_price import GetPriceUseCase
from src.shared.config import settings

# Singleton instances
_coingecko_client = None
_cache_service = None
_price_repository = None
_cache_warmer = None


async def get_coingecko_client() -> CoinGeckoClient:
    global _coingecko_client
    if _coingecko_client is None:
        _coingecko_client = CoinGeckoClient()
    return _coingecko_client


async def get_cache_service() -> CacheService:
    global _cache_service
    if _cache_service is None:
        memory_cache = OptimizedMemoryCache(
            ttl=settings.cache_ttl_l1,
            maxsize=settings.cache_max_size
        )
        _cache_service = CacheService(memory_cache)
    return _cache_service


async def get_price_repository() -> PriceRepository:
    global _price_repository
    if _price_repository is None:
        client = await get_coingecko_client()
        _price_repository = PriceRepository(client)
    return _price_repository


async def get_cache_warmer() -> CacheWarmer:
    global _cache_warmer
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer()
        repository = await get_price_repository()
        _cache_warmer.set_data_fetcher(repository.get_current_price)
        await _cache_warmer.start_warming()
    return _cache_warmer


async def get_price_use_case() -> GetPriceUseCase:
    repository = await get_price_repository()
    cache_service = await get_cache_service()
    # Убеждаемся, что прогрев запущен
    await get_cache_warmer()
    return GetPriceUseCase(repository, cache_service)