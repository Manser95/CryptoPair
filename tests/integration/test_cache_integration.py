import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime
import time


@pytest.mark.asyncio
class TestCacheIntegration:
    """Integration tests for cache behavior in the API"""
    
    async def test_cache_hit_performance(self, async_client: AsyncClient):
        """Test that cached responses are significantly faster"""
        mock_price = {
            "symbol": "eth",
            "vs_currency": "usdt",
            "price": 2500.50,
            "volume_24h": 1000000.0,
            "price_change_24h": 5.25,
            "last_updated": datetime.utcnow()
        }
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            
            # First call - simulate slow API call
            async def slow_first_call(*args, **kwargs):
                await asyncio.sleep(0.5)  # Simulate API delay
                return mock_price
            
            # Subsequent calls - fast cache hit
            mock_use_case.execute.side_effect = [
                slow_first_call("eth", "usdt"),
                mock_price,  # Cache hit
                mock_price,  # Cache hit
            ]
            mock_get_use_case.return_value = mock_use_case
            
            # First request (cache miss)
            start = time.time()
            response1 = await async_client.get("/api/v1/prices/eth-usdt")
            time1 = time.time() - start
            
            # Second request (cache hit)
            start = time.time()
            response2 = await async_client.get("/api/v1/prices/eth-usdt")
            time2 = time.time() - start
            
            # Third request (cache hit)
            start = time.time()
            response3 = await async_client.get("/api/v1/prices/eth-usdt")
            time3 = time.time() - start
            
            # All requests should be successful
            assert response1.status_code == 200
            assert response2.status_code == 200
            assert response3.status_code == 200
            
            # Cache hits should be at least 10x faster
            assert time2 < time1 / 10
            assert time3 < time1 / 10
    
    async def test_concurrent_cache_requests(self, async_client: AsyncClient):
        """Test that concurrent requests for same resource use cache efficiently"""
        mock_price = {
            "symbol": "btc",
            "vs_currency": "usdt",
            "price": 45000.0,
            "last_updated": datetime.utcnow()
        }
        
        call_count = 0
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            
            async def counting_call(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                await asyncio.sleep(0.1)  # Simulate API delay
                return mock_price
            
            mock_use_case.execute.side_effect = counting_call
            mock_get_use_case.return_value = mock_use_case
            
            # Make 10 concurrent requests
            tasks = [
                async_client.get("/api/v1/prices/btc-usdt")
                for _ in range(10)
            ]
            responses = await asyncio.gather(*tasks)
            
            # All should succeed
            assert all(r.status_code == 200 for r in responses)
            
            # Due to caching, the use case should be called much less than 10 times
            assert call_count < 5
    
    async def test_cache_expiration(self, async_client: AsyncClient):
        """Test that cache expires after TTL"""
        prices = [
            {"symbol": "sol", "vs_currency": "usdt", "price": 100.0, "last_updated": datetime.utcnow()},
            {"symbol": "sol", "vs_currency": "usdt", "price": 105.0, "last_updated": datetime.utcnow()},
        ]
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = prices
            mock_get_use_case.return_value = mock_use_case
            
            # First request
            response1 = await async_client.get("/api/v1/prices/sol-usdt")
            data1 = response1.json()
            assert data1["price"] == 100.0
            
            # Immediate second request (should be cached)
            response2 = await async_client.get("/api/v1/prices/sol-usdt")
            data2 = response2.json()
            assert data2["price"] == 100.0  # Same cached value
            
            # Wait for cache to expire (assuming 3-5 second TTL)
            await asyncio.sleep(6)
            
            # Third request (cache expired, should get new value)
            response3 = await async_client.get("/api/v1/prices/sol-usdt")
            data3 = response3.json()
            assert data3["price"] == 105.0  # New value
    
    async def test_different_pairs_cached_separately(self, async_client: AsyncClient):
        """Test that different trading pairs are cached separately"""
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            
            # Different prices for different pairs
            def price_by_pair(symbol, vs_currency):
                prices = {
                    ("eth", "usdt"): {"symbol": "eth", "vs_currency": "usdt", "price": 2500.0},
                    ("btc", "usdt"): {"symbol": "btc", "vs_currency": "usdt", "price": 45000.0},
                    ("bnb", "usdt"): {"symbol": "bnb", "vs_currency": "usdt", "price": 350.0},
                }
                return prices.get((symbol, vs_currency))
            
            mock_use_case.execute.side_effect = price_by_pair
            mock_get_use_case.return_value = mock_use_case
            
            # Request different pairs
            response1 = await async_client.get("/api/v1/prices/eth-usdt")
            response2 = await async_client.get("/api/v1/prices/btc-usdt")
            response3 = await async_client.get("/api/v1/prices/bnb-usdt")
            
            # Each should have its own cached value
            assert response1.json()["price"] == 2500.0
            assert response2.json()["price"] == 45000.0
            assert response3.json()["price"] == 350.0
    
    async def test_cache_under_load(self, async_client: AsyncClient):
        """Test cache behavior under simulated load"""
        mock_price = {
            "symbol": "eth",
            "vs_currency": "usdt", 
            "price": 2500.0,
            "last_updated": datetime.utcnow()
        }
        
        api_calls = 0
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            
            async def counting_api_call(*args, **kwargs):
                nonlocal api_calls
                api_calls += 1
                await asyncio.sleep(0.05)  # Simulate API delay
                return mock_price
            
            mock_use_case.execute.side_effect = counting_api_call
            mock_get_use_case.return_value = mock_use_case
            
            # Simulate 100 requests over 2 seconds
            start_time = time.time()
            tasks = []
            
            for i in range(100):
                if i % 10 == 0:
                    await asyncio.sleep(0.2)  # Spread requests over time
                tasks.append(async_client.get("/api/v1/prices/eth-usdt"))
            
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)
            
            # With 3-second cache TTL, we should have very few API calls
            assert api_calls < 5  # Should be 1-2 calls for 2 seconds of requests
            
            # Total time should be reasonable
            assert total_time < 3.0