import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from src.data_access.repositories.interfaces import ICacheRepository
from src.data_access.models.cache_model import CacheEntry
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class RedisCacheRepository(ICacheRepository):
    """Redis implementation of cache repository with distributed locking"""
    
    def __init__(self, default_ttl: int = None):
        self.default_ttl = default_ttl or settings.cache_ttl
        self._redis: Optional[redis.Redis] = None
        self._connected = False
    
    async def _get_redis(self) -> redis.Redis:
        """Get or create Redis connection"""
        if not self._redis or not self._connected:
            self._redis = redis.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=settings.redis_decode_responses,
                health_check_interval=30,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self._connected = True
            # Test connection
            await self._redis.ping()
            logger.info("Redis connection established")
        return self._redis
    
    async def start(self):
        """Initialize Redis connection"""
        await self._get_redis()
    
    async def stop(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Redis connection closed")
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache"""
        try:
            redis_client = await self._get_redis()
            
            # Get value and TTL in pipeline
            pipe = redis_client.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            result, ttl = await pipe.execute()
            
            if not result:
                return None
            
            # Parse JSON value
            value = json.loads(result)
            
            # Calculate expiry time
            expires_at = None
            if ttl > 0:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            
            # Create CacheEntry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow() - timedelta(seconds=self.default_ttl - ttl) if ttl > 0 else datetime.utcnow(),
                expires_at=expires_at
            )
            
            return entry
            
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL"""
        try:
            redis_client = await self._get_redis()
            ttl = ttl or self.default_ttl
            
            # Convert value to JSON
            json_value = json.dumps(value)
            
            # Set with TTL
            if ttl > 0:
                await redis_client.setex(key, ttl, json_value)
            else:
                await redis_client.set(key, json_value)
                
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            raise
    
    async def set_if_not_exists(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value only if key doesn't exist. Returns True if set, False if already exists"""
        try:
            redis_client = await self._get_redis()
            ttl = ttl or self.default_ttl
            
            # Convert value to JSON
            json_value = json.dumps(value)
            
            # Use SET NX with EX for atomic operation
            result = await redis_client.set(key, json_value, nx=True, ex=ttl if ttl > 0 else None)
            
            return result is True
            
        except Exception as e:
            logger.error(f"Error setting cache key {key} with NX: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            redis_client = await self._get_redis()
            return await redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Error checking existence of cache key {key}: {e}")
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries (use with caution in production)"""
        try:
            redis_client = await self._get_redis()
            await redis_client.flushdb()
            logger.warning("Redis cache cleared")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_client = await self._get_redis()
            
            # Get Redis info
            info = await redis_client.info()
            
            # Get database size
            db_size = await redis_client.dbsize()
            
            return {
                "type": "redis",
                "connected": self._connected,
                "db_size": db_size,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "hit_rate": self._calculate_hit_rate(info),
                "evicted_keys": info.get("evicted_keys", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"type": "redis", "connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, info: Dict[str, Any]) -> float:
        """Calculate cache hit rate from Redis info"""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
            
        return round((hits / total) * 100, 2)
    
    async def acquire_lock(self, lock_key: str, lock_timeout: int = 10, acquire_timeout: float = 5.0) -> bool:
        """
        Acquire a distributed lock using Redis.
        
        Args:
            lock_key: The key for the lock
            lock_timeout: How long the lock should be held (seconds)
            acquire_timeout: How long to wait trying to acquire the lock (seconds)
            
        Returns:
            True if lock acquired, False otherwise
        """
        try:
            redis_client = await self._get_redis()
            
            # Try to acquire lock with timeout
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).total_seconds() < acquire_timeout:
                # Try to set lock with NX (only if not exists) and EX (expiry)
                acquired = await redis_client.set(
                    f"lock:{lock_key}",
                    "1",
                    nx=True,
                    ex=lock_timeout
                )
                
                if acquired:
                    return True
                
                # Wait a bit before retrying
                await asyncio.sleep(0.05)
            
            return False
            
        except Exception as e:
            logger.error(f"Error acquiring lock {lock_key}: {e}")
            return False
    
    async def release_lock(self, lock_key: str) -> bool:
        """Release a distributed lock"""
        try:
            redis_client = await self._get_redis()
            result = await redis_client.delete(f"lock:{lock_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error releasing lock {lock_key}: {e}")
            return False


# Import asyncio for lock implementation
import asyncio