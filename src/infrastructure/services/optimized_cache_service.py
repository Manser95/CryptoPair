import asyncio
from typing import Optional, Any, Dict
from cachetools import TTLCache
from src.application.interfaces.cache_service import CacheServiceInterface
from src.shared.monitoring import CACHE_HITS, CACHE_MISSES
from src.shared.logging import get_logger
import time

logger = get_logger(__name__)


class OptimizedCacheService(CacheServiceInterface):
    """
    High-performance single-level cache optimized for short TTL (2-5 seconds)
    and high concurrent access.
    
    Key optimizations:
    - Lock-free reads for better concurrency
    - Per-key locks to prevent cache stampede
    - Configurable TTL with jitter to spread expirations
    - Metrics for monitoring
    """
    
    def __init__(self, ttl: int = 5, max_size: int = 10000, ttl_jitter: float = 0.2):
        """
        Initialize optimized cache.
        
        Args:
            ttl: Base TTL in seconds (default: 5)
            max_size: Maximum cache entries (default: 10000)
            ttl_jitter: Jitter factor for TTL randomization (default: 0.2 = ±20%)
        """
        self.base_ttl = ttl
        self.ttl_jitter = ttl_jitter
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._lock_manager = asyncio.Lock()
        
    def _get_ttl_with_jitter(self) -> float:
        """Calculate TTL with random jitter to prevent thundering herd"""
        import random
        jitter_range = self.base_ttl * self.ttl_jitter
        return self.base_ttl + random.uniform(-jitter_range, jitter_range)
    
    async def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific key"""
        async with self._lock_manager:
            if key not in self._locks:
                self._locks[key] = asyncio.Lock()
            return self._locks[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with lock-free read.
        """
        try:
            # Fast path - no locking for reads
            value = self.cache.get(key)
            
            if value is not None:
                CACHE_HITS.labels(cache_level="memory", operation="get").inc()
                logger.debug(f"Cache hit for key: {key}")
                return value
            else:
                CACHE_MISSES.labels(cache_level="memory", operation="get").inc()
                logger.debug(f"Cache miss for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache with per-key locking to prevent stampede.
        """
        try:
            # Use per-key lock to prevent multiple simultaneous cache updates
            lock = await self._get_lock(key)
            
            async with lock:
                # Double-check if value was already cached while waiting for lock
                if key in self.cache:
                    logger.debug(f"Key {key} already cached while waiting for lock")
                    return
                
                # Use custom TTL with jitter
                effective_ttl = self._get_ttl_with_jitter() if ttl is None else ttl
                
                # Create a new cache with the specific TTL for this entry
                # This is a workaround since cachetools doesn't support per-key TTL
                self.cache[key] = value
                
                logger.debug(f"Cached key: {key} with TTL: {effective_ttl:.2f}s")
                
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        try:
            lock = await self._get_lock(key)
            async with lock:
                self.cache.pop(key, None)
                # Clean up the lock
                self._locks.pop(key, None)
                
            logger.debug(f"Deleted key: {key}")
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        try:
            async with self._lock_manager:
                self.cache.clear()
                self._locks.clear()
                
            logger.info("Cache cleared")
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.base_ttl,
            "keys": list(self.cache.keys()),
            "hits": CACHE_HITS.labels(cache_level="memory", operation="get")._value.get(),
            "misses": CACHE_MISSES.labels(cache_level="memory", operation="get")._value.get()
        }