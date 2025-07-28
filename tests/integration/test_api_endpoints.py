import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime
from src.domain.entities.crypto_price import CryptoPrice


@pytest.mark.asyncio
class TestPriceEndpoints:
    """Integration tests for price API endpoints"""
    
    async def test_get_crypto_price_success(self, async_client: AsyncClient):
        """Test successful price retrieval"""
        # Mock the use case
        mock_price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=3900.0,
            volume_24h=1000000.0,
            price_change_24h=5.25,
            last_updated=datetime.utcnow()
        )
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_price
            mock_get_use_case.return_value = mock_use_case
            
            response = await async_client.get("/api/v1/prices/eth-usdt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "eth"
            assert data["vs_currency"] == "usdt"
            assert data["price"] == 3900.0
            assert data["pair"] == "ETH/USDT"
    
    async def test_get_crypto_price_not_found(self, async_client: AsyncClient):
        """Test price not found returns 404"""
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = None
            mock_get_use_case.return_value = mock_use_case
            
            response = await async_client.get("/api/v1/prices/invalid-coin")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()
    
    async def test_get_crypto_price_server_error(self, async_client: AsyncClient):
        """Test server error returns 500"""
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.side_effect = Exception("Database connection failed")
            mock_get_use_case.return_value = mock_use_case
            
            response = await async_client.get("/api/v1/prices/eth-usdt")
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Internal server error" in data["detail"]
    
    async def test_get_eth_usdt_shortcut(self, async_client: AsyncClient):
        """Test ETH/USDT shortcut endpoint"""
        mock_price = CryptoPrice(
            symbol="eth",
            vs_currency="usdt",
            price=3900.0,
            last_updated=datetime.utcnow()
        )
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_price
            mock_get_use_case.return_value = mock_use_case
            
            response = await async_client.get("/api/v1/prices/eth-usdt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["symbol"] == "eth"
            assert data["vs_currency"] == "usdt"
            mock_use_case.execute.assert_called_with("eth", "usdt")
    
    async def test_price_response_format(self, async_client: AsyncClient):
        """Test that price response matches expected schema"""
        mock_price = CryptoPrice(
            symbol="btc",
            vs_currency="usd",
            price=110000.0,
            volume_24h=50000000.0,
            price_change_24h=-2.5,
            last_updated=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
            mock_use_case = AsyncMock()
            mock_use_case.execute.return_value = mock_price
            mock_get_use_case.return_value = mock_use_case
            
            response = await async_client.get("/api/v1/prices/btc-usd")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check all fields are present
            assert "symbol" in data
            assert "vs_currency" in data
            assert "price" in data
            assert "volume_24h" in data
            assert "price_change_24h" in data
            assert "last_updated" in data
            assert "pair" in data
            
            # Check data types
            assert isinstance(data["price"], float)
            assert isinstance(data["volume_24h"], float)
            assert isinstance(data["price_change_24h"], float)
            assert isinstance(data["last_updated"], str)
    
    async def test_different_trading_pairs(self, async_client: AsyncClient):
        """Test various trading pair combinations"""
        test_pairs = [
            ("btc", "usd", 110000.0),
            ("eth", "eur", 3900.0),
            ("bnb", "usdt", 650.0),
            ("sol", "btc", 200.0)
        ]
        
        for symbol, vs_currency, price in test_pairs:
            mock_price = CryptoPrice(
                symbol=symbol,
                vs_currency=vs_currency,
                price=price
            )
            
            with patch('src.presentation.api.dependencies.get_price_use_case') as mock_get_use_case:
                mock_use_case = AsyncMock()
                mock_use_case.execute.return_value = mock_price
                mock_get_use_case.return_value = mock_use_case
                
                response = await async_client.get(f"/api/v1/prices/{symbol}-{vs_currency}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["symbol"] == symbol
                assert data["vs_currency"] == vs_currency
                assert data["price"] == price
                assert data["pair"] == f"{symbol.upper()}/{vs_currency.upper()}"