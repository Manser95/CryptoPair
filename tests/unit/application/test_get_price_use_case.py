import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from src.application.use_cases.get_price import GetPriceUseCase
from src.domain.entities.crypto_price import CryptoPrice


@pytest.mark.asyncio
class TestGetPriceUseCase:
    """Test cases for GetPriceUseCase"""
    
    async def test_get_price_from_cache(self, mock_cache_service, mock_price_repository):
        """Test getting price from cache when available"""
        # Arrange
        cached_data = {
            "symbol": "eth",
            "vs_currency": "usdt",
            "price": 2500.0,
            "volume_24h": 1000000.0,
            "price_change_24h": 5.25,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        mock_cache_service.get.return_value = cached_data
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        result = await use_case.execute("eth", "usdt")
        
        # Assert
        assert result is not None
        assert result.symbol == "eth"
        assert result.vs_currency == "usdt"
        assert result.price == 2500.0
        # Check that cache.get was called with key and refresh function
        assert mock_cache_service.get.call_count == 1
        assert mock_cache_service.get.call_args[0][0] == "price:eth:usdt"
        assert callable(mock_cache_service.get.call_args[0][1])
        mock_price_repository.get_current_price.assert_not_called()
    
    async def test_get_price_from_repository_when_cache_miss(self, mock_cache_service, mock_price_repository):
        """Test getting price from repository when not in cache"""
        # Arrange
        mock_cache_service.get.return_value = None
        expected_price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=2600.0,
            volume_24h=1100000.0,
            price_change_24h=6.0,
            last_updated=datetime.now(timezone.utc)
        )
        mock_price_repository.get_current_price.return_value = expected_price
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        result = await use_case.execute("eth", "usdt")
        
        # Assert
        assert result == expected_price
        # Check that cache.get was called with key and refresh function
        assert mock_cache_service.get.call_count == 1
        assert mock_cache_service.get.call_args[0][0] == "price:eth:usdt"
        assert callable(mock_cache_service.get.call_args[0][1])
        mock_price_repository.get_current_price.assert_called_once_with("eth", "usdt")
        mock_cache_service.set.assert_called_once_with(
            "price:eth:usdt",
            expected_price.to_dict()
        )
    
    async def test_get_price_returns_none_when_not_found(self, mock_cache_service, mock_price_repository):
        """Test that None is returned when price is not found"""
        # Arrange
        mock_cache_service.get.return_value = None
        mock_price_repository.get_current_price.return_value = None
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        result = await use_case.execute("invalid", "coin")
        
        # Assert
        assert result is None
        mock_cache_service.get.assert_called_once()
        mock_price_repository.get_current_price.assert_called_once()
        mock_cache_service.set.assert_not_called()
    
    async def test_get_price_handles_cache_with_pair_field(self, mock_cache_service, mock_price_repository):
        """Test that cached data with 'pair' field is handled correctly"""
        # Arrange
        cached_data = {
            "symbol": "btc",
            "vs_currency": "usd",
            "price": 45000.0,
            "pair": "BTC/USD",  # This field should be removed
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        mock_cache_service.get.return_value = cached_data
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        result = await use_case.execute("btc", "usd")
        
        # Assert
        assert result is not None
        assert result.symbol == "btc"
        assert result.vs_currency == "usd"
        assert result.price == 45000.0
        assert not hasattr(result, 'pair')
    
    async def test_get_price_cache_key_format(self, mock_cache_service, mock_price_repository):
        """Test that cache key is formatted correctly"""
        # Arrange
        mock_cache_service.get.return_value = None
        mock_price_repository.get_current_price.return_value = None
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        await use_case.execute("ETH", "USDT")
        
        # Assert
        # Check that cache.get was called with key and refresh function
        assert mock_cache_service.get.call_count == 1
        assert mock_cache_service.get.call_args[0][0] == "price:ETH:USDT"
        assert callable(mock_cache_service.get.call_args[0][1])
    
    async def test_get_price_handles_datetime_conversion(self, mock_cache_service, mock_price_repository):
        """Test that datetime string is converted back to datetime object"""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        cached_data = {
            "symbol": "eth",
            "vs_currency": "usdt",
            "price": 2500.0,
            "last_updated": timestamp.isoformat()
        }
        mock_cache_service.get.return_value = cached_data
        
        use_case = GetPriceUseCase(mock_price_repository, mock_cache_service)
        
        # Act
        result = await use_case.execute("eth", "usdt")
        
        # Assert
        assert result is not None
        assert isinstance(result.last_updated, datetime)
        assert result.last_updated.isoformat() == timestamp.isoformat()