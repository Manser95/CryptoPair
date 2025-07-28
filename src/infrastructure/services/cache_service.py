from typing import Optional, Any
from src.application.interfaces.cache_service import CacheServiceInterface
from src.infrastructure.cache.memory_cache import MemoryCache
from src.infrastructure.cache.redis_cache import RedisCache
from src.shared.monitoring import CACHE_HITS, CACHE_MISSES
from src.shared.logging import get_logger

logger = get_logger(__name__)


class MultiLevelCacheService(CacheServiceInterface):
    """Multi-level cache implementation with L1 (memory) and L2 (Redis)"""
    
    def __init__(self, memory_cache: MemoryCache, redis_cache: RedisCache):
        self.l1_cache = memory_cache
        self.l2_cache = redis_cache
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, checking L1 first, then L2"""
        # Check L1 cache
        value = await self.l1_cache.get(key)
        if value is not None:
            CACHE_HITS.labels(cache_level="L1", operation="get").inc()
            return value
        
        CACHE_MISSES.labels(cache_level="L1", operation="get").inc()
        
        # Check L2 cache
        value = await self.l2_cache.get(key)
        if value is not None:
            CACHE_HITS.labels(cache_level="L2", operation="get").inc()
            # Populate L1 cache
            await self.l1_cache.set(key, value)
            return value
        
        CACHE_MISSES.labels(cache_level="L2", operation="get").inc()
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in both cache levels"""
        # Set in both caches
        await self.l1_cache.set(key, value)
        await self.l2_cache.set(key, value)
        
        logger.debug(f"Set value in both cache levels for key: {key}")
    
    async def delete(self, key: str) -> None:
        """Delete value from both cache levels"""
        await self.l1_cache.delete(key)
        await self.l2_cache.delete(key)
        
        logger.debug(f"Deleted value from both cache levels for key: {key}")
    
    async def clear(self) -> None:
        """Clear both cache levels"""
        await self.l1_cache.clear()
        await self.l2_cache.clear()
        
        logger.info("Cleared both cache levels")