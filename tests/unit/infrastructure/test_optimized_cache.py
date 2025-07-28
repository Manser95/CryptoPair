import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock
from src.infrastructure.services.optimized_cache_service import OptimizedCacheService


@pytest.mark.asyncio
class TestOptimizedCacheService:
    """Test cases for OptimizedCacheService"""
    
    async def test_initialization(self):
        """Test cache initialization with default and custom values"""
        # Default values
        cache = OptimizedCacheService()
        assert cache.base_ttl == 5
        assert cache.ttl_jitter == 0.2
        assert cache.cache.maxsize == 10000
        
        # Custom values
        cache_custom = OptimizedCacheService(ttl=3, max_size=5000, ttl_jitter=0.1)
        assert cache_custom.base_ttl == 3
        assert cache_custom.ttl_jitter == 0.1
        assert cache_custom.cache.maxsize == 5000
    
    async def test_get_and_set(self):
        """Test basic get and set operations"""
        cache = OptimizedCacheService(ttl=5)
        
        # Set value
        await cache.set("test_key", {"value": "test_data"})
        
        # Get value
        result = await cache.get("test_key")
        assert result == {"value": "test_data"}
    
    async def test_cache_miss(self):
        """Test cache miss returns None"""
        cache = OptimizedCacheService()
        
        result = await cache.get("non_existent_key")
        assert result is None
    
    async def test_ttl_with_jitter(self):
        """Test that TTL includes jitter"""
        cache = OptimizedCacheService(ttl=5, ttl_jitter=0.2)
        
        # Mock random to control jitter
        with patch('random.uniform', return_value=0.5):
            await cache.set("test_key", "test_value")
            
            # The effective TTL should be base_ttl + jitter
            # With base_ttl=5 and jitter=0.2, random.uniform(0, 1) * 0.2 = 0.1
            # So effective TTL = 5 + 0.1 = 5.1
    
    async def test_concurrent_access_same_key(self):
        """Test that concurrent access to same key uses locking"""
        cache = OptimizedCacheService()
        
        # Track call count
        call_count = 0
        
        async def slow_getter():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)
            return {"count": call_count}
        
        # Set up cache to miss first
        result = await cache.get("concurrent_key")
        assert result is None
        
        # Now set a value
        await cache.set("concurrent_key", {"initial": "value"})
        
        # Concurrent reads should all get the same value
        results = await asyncio.gather(
            cache.get("concurrent_key"),
            cache.get("concurrent_key"),
            cache.get("concurrent_key")
        )
        
        assert all(r == {"initial": "value"} for r in results)
    
    async def test_delete_operation(self):
        """Test delete removes key from cache"""
        cache = OptimizedCacheService()
        
        # Set and verify
        await cache.set("delete_key", "value")
        assert await cache.get("delete_key") == "value"
        
        # Delete and verify
        await cache.delete("delete_key")
        assert await cache.get("delete_key") is None
    
    async def test_clear_operation(self):
        """Test clear removes all keys"""
        cache = OptimizedCacheService()
        
        # Set multiple keys
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Clear cache
        await cache.clear()
        
        # Verify all keys are gone
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is None
    
    async def test_get_stats(self):
        """Test cache statistics"""
        cache = OptimizedCacheService()
        
        # Initial stats
        stats = cache.get_stats()
        assert stats["size"] == 0
        assert stats["max_size"] == 10000
        assert stats["ttl"] == 5
        
        # Add some items
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        
        stats = cache.get_stats()
        assert stats["size"] == 2
        assert stats["keys"] == ["key1", "key2"]
    
    async def test_lock_cleanup(self):
        """Test that locks are cleaned up to prevent memory leaks"""
        cache = OptimizedCacheService()
        
        # Create many locks
        for i in range(1000):
            await cache.get(f"key_{i}")
        
        # Locks should be cleaned up periodically
        assert len(cache._locks) <= 100  # Cleanup threshold
    
    async def test_ttl_expiration(self):
        """Test that items expire after TTL"""
        cache = OptimizedCacheService(ttl=1)  # 1 second TTL
        
        await cache.set("expire_key", "value")
        
        # Should exist immediately
        assert await cache.get("expire_key") == "value"
        
        # Wait for expiration
        await asyncio.sleep(1.5)
        
        # Should be expired
        assert await cache.get("expire_key") is None
    
    @patch('src.infrastructure.services.optimized_cache_service.CACHE_HITS')
    @patch('src.infrastructure.services.optimized_cache_service.CACHE_MISSES')
    async def test_metrics_tracking(self, mock_misses, mock_hits):
        """Test that cache hits and misses are tracked"""
        # Set up the mock labels to return a mock that has inc() method
        mock_misses_label = MagicMock()
        mock_hits_label = MagicMock()
        mock_misses.labels.return_value = mock_misses_label
        mock_hits.labels.return_value = mock_hits_label
        
        cache = OptimizedCacheService()
        
        # Cache miss
        await cache.get("missing_key")
        mock_misses.labels.assert_called_once_with(cache_level="memory", operation="get")
        mock_misses_label.inc.assert_called_once()
        
        # Cache hit
        await cache.set("hit_key", "value")
        await cache.get("hit_key")
        mock_hits.labels.assert_called_once_with(cache_level="memory", operation="get")
        mock_hits_label.inc.assert_called_once()
    
    async def test_various_data_types(self):
        """Test caching various data types"""
        cache = OptimizedCacheService()
        
        test_data = [
            ("string", "test_string"),
            ("int", 42),
            ("float", 3.14),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value", "nested": {"data": 123}}),
            ("bool", True),
            ("none", None),
        ]
        
        for key, value in test_data:
            await cache.set(key, value)
            result = await cache.get(key)
            assert result == value, f"Failed for type {key}"