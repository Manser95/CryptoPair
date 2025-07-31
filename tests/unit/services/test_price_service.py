import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from src.services.price_service import PriceService
from src.data_access.models.price_model import PriceData


@pytest.mark.asyncio
class TestPriceService:
    """Unit tests for PriceService"""
    
    @pytest.fixture
    def mock_cache_service(self):
        return AsyncMock()
    
    @pytest.fixture
    def mock_price_repository(self):
        return AsyncMock()
    
    @pytest.fixture
    def price_service(self, mock_cache_service, mock_price_repository):
        return PriceService(mock_cache_service, mock_price_repository)
    
    async def test_get_price_from_cache(self, price_service, mock_cache_service, sample_price_data):
        """Test getting price from cache when available"""
        mock_cache_service.get.return_value = sample_price_data
        
        result = await price_service.get_crypto_price("eth", "usdt")
        
        assert result == sample_price_data
        mock_cache_service.get.assert_called_once_with("price:eth:usdt")
        # Repository should not be called if cache hit
        price_service.price_repository.get_price.assert_not_called()
    
    async def test_get_price_from_repository(self, price_service, mock_cache_service, mock_price_repository, sample_price_data):
        """Test getting price from repository when not in cache"""
        mock_cache_service.get.return_value = None
        mock_price_repository.get_price.return_value = sample_price_data
        
        result = await price_service.get_crypto_price("eth", "usdt")
        
        assert result == sample_price_data
        mock_cache_service.get.assert_called_once_with("price:eth:usdt")
        mock_price_repository.get_price.assert_called_once_with("eth", "usdt")
        # Should cache the result
        mock_cache_service.set.assert_called_once()
    
    async def test_get_price_not_found(self, price_service, mock_cache_service, mock_price_repository):
        """Test when price is not found"""
        mock_cache_service.get.return_value = None
        mock_price_repository.get_price.return_value = None
        
        result = await price_service.get_crypto_price("invalid", "coin")
        
        assert result is None
        mock_cache_service.set.assert_not_called()