import pytest
import asyncio
from unittest.mock import patch, MagicMock
from src.infrastructure.cache.memory_cache import MemoryCache


@pytest.mark.asyncio
class TestMemoryCache:
    """Test cases for MemoryCache"""
    
    async def test_memory_cache_initialization(self):
        """Test MemoryCache initialization with default and custom values"""
        # With default values
        cache = MemoryCache()
        assert cache.ttl == 5  # Default from settings
        assert cache.cache.maxsize == 1000
        
        # With custom values
        cache_custom = MemoryCache(ttl=10, maxsize=500)
        assert cache_custom.ttl == 10
        assert cache_custom.cache.maxsize == 500
    
    async def test_get_existing_key(self):
        """Test getting an existing key from cache"""
        cache = MemoryCache()
        await cache.set("test_key", "test_value")
        
        result = await cache.get("test_key")
        assert result == "test_value"
    
    async def test_get_non_existing_key(self):
        """Test getting a non-existing key returns None"""
        cache = MemoryCache()
        
        result = await cache.get("non_existing_key")
        assert result is None
    
    async def test_set_and_get_various_types(self):
        """Test setting and getting various data types"""
        cache = MemoryCache()
        
        # String
        await cache.set("string_key", "string_value")
        assert await cache.get("string_key") == "string_value"
        
        # Integer
        await cache.set("int_key", 42)
        assert await cache.get("int_key") == 42
        
        # Float
        await cache.set("float_key", 3.14)
        assert await cache.get("float_key") == 3.14
        
        # Dict
        test_dict = {"name": "test", "value": 123}
        await cache.set("dict_key", test_dict)
        assert await cache.get("dict_key") == test_dict
        
        # List
        test_list = [1, 2, 3, "test"]
        await cache.set("list_key", test_list)
        assert await cache.get("list_key") == test_list
    
    async def test_delete_key(self):
        """Test deleting a key from cache"""
        cache = MemoryCache()
        await cache.set("test_key", "test_value")
        
        # Verify key exists
        assert await cache.get("test_key") == "test_value"
        
        # Delete key
        await cache.delete("test_key")
        
        # Verify key is deleted
        assert await cache.get("test_key") is None
    
    async def test_delete_non_existing_key(self):
        """Test deleting a non-existing key doesn't raise error"""
        cache = MemoryCache()
        
        # Should not raise any exception
        await cache.delete("non_existing_key")
    
    async def test_clear_cache(self):
        """Test clearing all keys from cache"""
        cache = MemoryCache()
        
        # Add multiple keys
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # Verify keys exist
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        
        # Clear cache
        await cache.clear()
        
        # Verify all keys are removed
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
        assert await cache.get("key3") is None
    
    async def test_ttl_expiration(self):
        """Test that cached values expire after TTL"""
        cache = MemoryCache(ttl=1)  # 1 second TTL
        
        await cache.set("test_key", "test_value")
        
        # Value should be available immediately
        assert await cache.get("test_key") == "test_value"
        
        # Wait for TTL to expire
        await asyncio.sleep(1.1)
        
        # Value should be expired
        assert await cache.get("test_key") is None
    
    async def test_maxsize_eviction(self):
        """Test that cache evicts items when maxsize is reached"""
        cache = MemoryCache(maxsize=3)
        
        # Add items up to maxsize
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")
        
        # All should be present
        assert await cache.get("key1") == "value1"
        assert await cache.get("key2") == "value2"
        assert await cache.get("key3") == "value3"
        
        # Add one more item (should evict the least recently used)
        await cache.set("key4", "value4")
        
        # key4 should be present, but one of the others might be evicted
        assert await cache.get("key4") == "value4"
        
        # Verify cache size doesn't exceed maxsize
        assert len(cache.cache) <= 3
    
    async def test_update_existing_key(self):
        """Test updating an existing key in cache"""
        cache = MemoryCache()
        
        # Set initial value
        await cache.set("test_key", "initial_value")
        assert await cache.get("test_key") == "initial_value"
        
        # Update value
        await cache.set("test_key", "updated_value")
        assert await cache.get("test_key") == "updated_value"
    
    @patch('src.infrastructure.cache.memory_cache.logger')
    async def test_logging(self, mock_logger):
        """Test that appropriate log messages are generated"""
        cache = MemoryCache()
        
        # Test cache miss logging
        await cache.get("non_existing")
        mock_logger.debug.assert_called_with("L1 cache miss for key: non_existing")
        
        # Test cache set logging
        await cache.set("test_key", "test_value")
        mock_logger.debug.assert_called_with("L1 cache set for key: test_key")
        
        # Test cache hit logging
        await cache.get("test_key")
        mock_logger.debug.assert_called_with("L1 cache hit for key: test_key")
        
        # Test cache delete logging
        await cache.delete("test_key")
        mock_logger.debug.assert_called_with("L1 cache delete for key: test_key")
        
        # Test cache clear logging
        await cache.clear()
        mock_logger.info.assert_called_with("L1 cache cleared")