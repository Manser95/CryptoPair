from typing import Any, Optional, Callable
from src.data_access.repositories.interfaces import ICacheRepository
from src.data_access.models.cache_model import CacheEntry
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CacheService:
    """
    Service layer for cache operations.
    Provides high-level cache functionality including stale-while-revalidate pattern.
    """
    
    def __init__(self, cache_repository: ICacheRepository):
        """
        Initialize cache service.
        
        Args:
            cache_repository: Repository for cache operations
        """
        self.cache_repository = cache_repository
        
        # Configuration
        self.default_ttl = 300  # 5 minutes
        self.stale_multiplier = 2  # Serve stale data for 2x TTL
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: Optional[int] = None,
        use_stale: bool = True
    ) -> Optional[Any]:
        """
        Get value from cache or fetch using provided function.
        
        Args:
            key: Cache key
            fetch_func: Function to call if cache miss
            ttl: Time to live in seconds
            use_stale: Whether to use stale-while-revalidate pattern
            
        Returns:
            Cached or fetched value
        """
        ttl = ttl or self.default_ttl
        
        # Try to get from cache
        entry = await self.cache_repository.get(key)
        
        if entry:
            # Fresh data
            if not entry.is_expired:
                return entry.value
            
            # Stale data
            if use_stale and entry.age_seconds < (ttl * self.stale_multiplier):
                # Return stale data without background refresh
                return entry.value
        
        # Fetch new data
        try:
            value = await fetch_func()
            if value is not None:
                await self.cache_repository.set(key, value, ttl)
            return value
        except Exception as e:
            logger.error(f"Failed to fetch data for key {key}: {e}")
            
            # Return stale data on error if available
            if entry and use_stale:
                logger.warning(f"Returning stale data for {key} due to fetch error")
                return entry.value
            
            raise
    
    
    async def invalidate(self, key: str) -> bool:
        """
        Invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if entry was deleted, False if not found
        """
        return await self.cache_repository.delete(key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all cache entries matching a pattern.
        
        Args:
            pattern: Pattern to match (e.g., "price:*")
            
        Returns:
            Number of entries invalidated
        """
        # This is a simple implementation - in production you might want
        # to use Redis with SCAN command for pattern matching
        count = 0
        if hasattr(self.cache_repository, '_cache'):
            keys_to_delete = []
            async with self.cache_repository._lock:
                for key in self.cache_repository._cache.keys():
                    if self._match_pattern(key, pattern):
                        keys_to_delete.append(key)
            
            for key in keys_to_delete:
                if await self.cache_repository.delete(key):
                    count += 1
        
        logger.info(f"Invalidated {count} cache entries matching pattern {pattern}")
        return count
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        import fnmatch
        return fnmatch.fnmatch(key, pattern)
    
    async def set_with_tags(
        self,
        key: str,
        value: Any,
        tags: list[str],
        ttl: Optional[int] = None
    ) -> None:
        """
        Set cache entry with tags for group invalidation.
        
        Args:
            key: Cache key
            value: Value to cache
            tags: List of tags
            ttl: Time to live
        """
        # Store value
        await self.cache_repository.set(key, value, ttl or self.default_ttl)
        
        # Store tags (simplified - in production use a proper tag system)
        for tag in tags:
            tag_key = f"tag:{tag}:{key}"
            await self.cache_repository.set(tag_key, True, ttl or self.default_ttl)
    
    async def invalidate_by_tag(self, tag: str) -> int:
        """
        Invalidate all cache entries with a specific tag.
        
        Args:
            tag: Tag to invalidate
            
        Returns:
            Number of entries invalidated
        """
        pattern = f"tag:{tag}:*"
        return await self.invalidate_pattern(pattern)
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        base_stats = await self.cache_repository.get_stats() if hasattr(self.cache_repository, 'get_stats') else {}
        
        return {
            **base_stats,
            "default_ttl": self.default_ttl,
            "stale_multiplier": self.stale_multiplier
        }