from typing import Optional, Any
from src.application.interfaces.cache_service import CacheServiceInterface
from src.infrastructure.cache.optimized_memory_cache import OptimizedMemoryCache
from src.shared.monitoring import CACHE_HITS, CACHE_MISSES
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CacheService(CacheServiceInterface):
    """Оптимизированный memory-only cache service"""
    
    def __init__(self, memory_cache: OptimizedMemoryCache):
        self.cache = memory_cache
    
    async def get(self, key: str, refresh_func=None) -> Optional[Any]:
        """Get value from memory cache with stale-while-revalidate"""
        value = await self.cache.get(key, refresh_func)
        if value is not None:
            CACHE_HITS.labels(cache_level="L1", operation="get").inc()
            return value
        
        CACHE_MISSES.labels(cache_level="L1", operation="get").inc()
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache"""
        await self.cache.set(key, value)
        logger.debug(f"Set value in cache for key: {key}")
    
    async def delete(self, key: str) -> None:
        """Delete value from memory cache"""
        await self.cache.delete(key)
        logger.debug(f"Deleted value from cache for key: {key}")
    
    async def clear(self) -> None:
        """Clear memory cache"""
        await self.cache.clear()
        logger.info("Cleared cache")
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return self.cache.get_stats()