import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.infrastructure.api_clients.coingecko_client import CoinGeckoClient


@pytest.mark.asyncio
class TestCoinGeckoClient:
    """Test cases for CoinGeckoClient"""
    
    def test_initialization_without_api_key(self):
        """Test client initialization without API key"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            assert client.base_url == "https://api.coingecko.com/api/v3"
            assert client.api_key is None
    
    def test_initialization_with_api_key(self):
        """Test client initialization with API key"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = "CG-test-api-key"
            
            client = CoinGeckoClient()
            assert client.base_url == "https://pro-api.coingecko.com/api/v3"
            assert client.api_key == "CG-test-api-key"
    
    def test_get_headers_without_api_key(self):
        """Test headers generation without API key"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            
            client = CoinGeckoClient()
            headers = client._get_headers()
            
            assert headers == {
                "Accept": "application/json",
                "User-Agent": "CryptoPairsAPI/1.0"
            }
    
    def test_get_headers_with_api_key(self):
        """Test headers generation with API key"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = "CG-test-api-key"
            
            client = CoinGeckoClient()
            headers = client._get_headers()
            
            assert headers == {
                "Accept": "application/json",
                "User-Agent": "CryptoPairsAPI/1.0",
                "x-cg-demo-api-key": "CG-test-api-key"
            }
    
    async def test_get_simple_price_success(self):
        """Test successful price fetching"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            
            # Mock the request method
            mock_response = {
                "ethereum": {
                    "usd": 2500.50,
                    "usd_24h_vol": 1000000.0,
                    "usd_24h_change": 5.25,
                    "last_updated_at": 1641234567
                }
            }
            client.request = AsyncMock(return_value=mock_response)
            
            result = await client.get_simple_price(
                ids="ethereum",
                vs_currencies="usd",
                include_24hr_vol=True,
                include_24hr_change=True,
                include_last_updated_at=True
            )
            
            assert result == mock_response
            client.request.assert_called_once_with(
                method="GET",
                url="https://api.coingecko.com/api/v3/simple/price",
                headers=client._get_headers(),
                params={
                    "ids": "ethereum",
                    "vs_currencies": "usd",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                    "include_last_updated_at": "true"
                }
            )
    
    async def test_get_simple_price_minimal_params(self):
        """Test price fetching with minimal parameters"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            client.request = AsyncMock(return_value={})
            
            await client.get_simple_price(
                ids="bitcoin",
                vs_currencies="eur",
                include_24hr_vol=False,
                include_24hr_change=False,
                include_last_updated_at=False
            )
            
            client.request.assert_called_once_with(
                method="GET",
                url="https://api.coingecko.com/api/v3/simple/price",
                headers=client._get_headers(),
                params={
                    "ids": "bitcoin",
                    "vs_currencies": "eur"
                }
            )
    
    async def test_get_simple_price_error_handling(self):
        """Test error handling in price fetching"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            client.request = AsyncMock(side_effect=Exception("API Error"))
            
            with pytest.raises(Exception) as exc_info:
                await client.get_simple_price("ethereum", "usd")
            
            assert str(exc_info.value) == "API Error"
    
    async def test_get_coin_market_chart_success(self):
        """Test successful market chart fetching"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            
            mock_response = {
                "prices": [[1641234567000, 2500.50]],
                "market_caps": [[1641234567000, 300000000000]],
                "total_volumes": [[1641234567000, 1000000000]]
            }
            client.request = AsyncMock(return_value=mock_response)
            
            result = await client.get_coin_market_chart(
                coin_id="ethereum",
                vs_currency="usd",
                days=1,
                interval="hourly"
            )
            
            assert result == mock_response
            client.request.assert_called_once_with(
                method="GET",
                url="https://api.coingecko.com/api/v3/coins/ethereum/market_chart",
                headers=client._get_headers(),
                params={
                    "vs_currency": "usd",
                    "days": 1,
                    "interval": "hourly"
                }
            )
    
    async def test_get_coin_market_chart_without_interval(self):
        """Test market chart fetching without interval parameter"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            client.request = AsyncMock(return_value={})
            
            await client.get_coin_market_chart(
                coin_id="bitcoin",
                vs_currency="eur",
                days=7
            )
            
            client.request.assert_called_once_with(
                method="GET",
                url="https://api.coingecko.com/api/v3/coins/bitcoin/market_chart",
                headers=client._get_headers(),
                params={
                    "vs_currency": "eur",
                    "days": 7
                }
            )
    
    async def test_get_coin_market_chart_error_handling(self):
        """Test error handling in market chart fetching"""
        with patch('src.infrastructure.api_clients.coingecko_client.settings') as mock_settings:
            mock_settings.coingecko_api_key = None
            mock_settings.coingecko_base_url = "https://api.coingecko.com/api/v3"
            
            client = CoinGeckoClient()
            client.request = AsyncMock(side_effect=Exception("Network Error"))
            
            with pytest.raises(Exception) as exc_info:
                await client.get_coin_market_chart("ethereum", "usd", 1)
            
            assert str(exc_info.value) == "Network Error"