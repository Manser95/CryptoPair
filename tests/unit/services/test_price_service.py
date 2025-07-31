import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from src.services.price_service import PriceService
from src.data_access.models.price_model import PriceModel


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
        return PriceService(mock_price_repository, mock_cache_service)
    
    async def test_get_price_from_cache(self, price_service, mock_cache_service):
        """Test getting price from cache when available"""
        sample_price = PriceModel(
            symbol="eth",
            vs_currency="usdt", 
            price=3859.33,
            fetched_at=datetime.now(timezone.utc)
        )
        
        # Mock cache entry with fresh data
        mock_cache_entry = AsyncMock()
        mock_cache_entry.age_seconds = 3  # Fresh (less than 5s TTL)
        mock_cache_entry.value = sample_price.to_dict()
        mock_cache_service.get.return_value = mock_cache_entry
        
        result = await price_service.get_current_price("eth", "usdt")
        
        assert result.symbol == sample_price.symbol
        assert result.price == sample_price.price
        mock_cache_service.get.assert_called_once_with("price:eth:usdt")
        # Repository should not be called if cache hit
        price_service.price_repository.get_current_price.assert_not_called()
    
    async def test_get_price_from_repository(self, price_service, mock_cache_service, mock_price_repository):
        """Test getting price from repository when not in cache"""
        sample_price = PriceModel(
            symbol="eth",
            vs_currency="usdt",
            price=3859.33,
            fetched_at=datetime.now(timezone.utc)
        )
        
        mock_cache_service.get.return_value = None
        mock_price_repository.get_current_price.return_value = sample_price
        
        result = await price_service.get_current_price("eth", "usdt")
        
        assert result == sample_price
        mock_cache_service.get.assert_called_once_with("price:eth:usdt")
        mock_price_repository.get_current_price.assert_called_once_with("eth", "usdt")
        # Should cache the result
        mock_cache_service.set.assert_called_once()
    
    async def test_get_price_not_found(self, price_service, mock_cache_service, mock_price_repository):
        """Test when price is not found"""
        mock_cache_service.get.return_value = None
        mock_price_repository.get_current_price.return_value = None
        
        result = await price_service.get_current_price("invalid", "coin")
        
        assert result is None
        mock_cache_service.set.assert_not_called()