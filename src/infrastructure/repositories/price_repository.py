from typing import Optional
from datetime import datetime
from src.application.interfaces.price_repository import PriceRepositoryInterface
from src.domain.entities.crypto_price import CryptoPrice
from src.infrastructure.api_clients.coingecko_client import CoinGeckoClient
from src.infrastructure.circuit_breaker.breaker import CircuitBreaker
from src.infrastructure.resilience.retry_strategies import exponential_backoff_retry
from src.shared.monitoring import track_external_api_metrics
from src.shared.logging import get_logger

logger = get_logger(__name__)


class PriceRepository(PriceRepositoryInterface):
    def __init__(self, coingecko_client: CoinGeckoClient):
        self.client = coingecko_client
        self.circuit_breaker = CircuitBreaker()
    
    @exponential_backoff_retry(exceptions=Exception)
    @track_external_api_metrics(api="coingecko", endpoint="simple/price")
    async def get_current_price(self, symbol: str, vs_currency: str) -> Optional[CryptoPrice]:
        """Get current price from CoinGecko API with resilience patterns"""
        
        # Map common symbols to CoinGecko IDs
        symbol_mapping = {
            "eth": "ethereum",
            "btc": "bitcoin",
            "usdt": "tether",
            "usdc": "usd-coin"
        }
        
        # Check if vs_currency is a cryptocurrency
        crypto_currencies = ["usdt", "usdc", "btc", "eth", "bnb"]
        
        coin_id = symbol_mapping.get(symbol.lower(), symbol.lower())
        
        async def fetch_price():
            # For crypto-to-crypto pairs (like ETH/USDT), we need to get both prices in USD
            if vs_currency.lower() in crypto_currencies:
                vs_coin_id = symbol_mapping.get(vs_currency.lower(), vs_currency.lower())
                
                # Get both prices in USD
                data = await self.client.get_simple_price(
                    ids=f"{coin_id},{vs_coin_id}",
                    vs_currencies="usd",
                    include_24hr_vol=True,
                    include_24hr_change=True,
                    include_last_updated_at=True
                )
                
                if coin_id in data and vs_coin_id in data:
                    base_price_usd = data[coin_id]["usd"]
                    quote_price_usd = data[vs_coin_id]["usd"]
                    
                    # Calculate the cross rate
                    price = base_price_usd / quote_price_usd if quote_price_usd > 0 else 0
                    
                    return CryptoPrice(
                        symbol=symbol,
                        vs_currency=vs_currency,
                        price=price,
                        volume_24h=data[coin_id].get("usd_24h_vol"),
                        price_change_24h=data[coin_id].get("usd_24h_change"),
                        last_updated=datetime.fromtimestamp(data[coin_id].get("last_updated_at", 0))
                    )
            else:
                # For fiat pairs, use direct conversion
                data = await self.client.get_simple_price(
                    ids=coin_id,
                    vs_currencies=vs_currency.lower(),
                    include_24hr_vol=True,
                    include_24hr_change=True,
                    include_last_updated_at=True
                )
                
                if coin_id in data:
                    price_data = data[coin_id]
                    return CryptoPrice(
                        symbol=symbol,
                        vs_currency=vs_currency,
                        price=price_data.get(vs_currency.lower(), 0),
                        volume_24h=price_data.get(f"{vs_currency.lower()}_24h_vol"),
                        price_change_24h=price_data.get(f"{vs_currency.lower()}_24h_change"),
                        last_updated=datetime.fromtimestamp(price_data.get("last_updated_at", 0))
                    )
            
            return None
        
        try:
            return await self.circuit_breaker.call(fetch_price)
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}/{vs_currency}: {e}")
            raise
    
    async def get_price_history(self, symbol: str, vs_currency: str, days: int) -> list:
        """Get price history from CoinGecko API"""
        # Map common symbols to CoinGecko IDs
        symbol_mapping = {
            "eth": "ethereum",
            "btc": "bitcoin",
            "usdt": "tether"
        }
        
        # Map currency symbols
        currency_mapping = {
            "usdt": "usd",  # CoinGecko uses 'usd' not 'usdt'
            "usdc": "usd"
        }
        
        coin_id = symbol_mapping.get(symbol.lower(), symbol.lower())
        mapped_currency = currency_mapping.get(vs_currency.lower(), vs_currency.lower())
        
        async def fetch_history():
            data = await self.client.get_coin_market_chart(
                coin_id=coin_id,
                vs_currency=mapped_currency,
                days=days
            )
            
            return data.get("prices", [])
        
        try:
            return await self.circuit_breaker.call(fetch_history)
        except Exception as e:
            logger.error(f"Failed to get price history for {symbol}/{vs_currency}: {e}")
            raise