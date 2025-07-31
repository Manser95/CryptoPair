from typing import Optional
from datetime import datetime
from src.data_access.repositories.interfaces import IPriceRepository
from src.data_access.models.price_model import PriceModel
from src.data_access.external.coingecko_gateway import CoinGeckoGateway
from src.shared.logging import get_logger

logger = get_logger(__name__)


class PriceRepository(IPriceRepository):
    """Repository for accessing price data from external sources"""
    
    def __init__(self, gateway: CoinGeckoGateway):
        self.gateway = gateway
        self.symbol_mapping = {
            "eth": "ethereum",
            "btc": "bitcoin",
            "usdt": "tether",
            "usdc": "usd-coin"
        }
        self.crypto_currencies = ["usdt", "usdc", "btc", "eth"]
    
    async def get_current_price(self, symbol: str, vs_currency: str) -> Optional[PriceModel]:
        """Get current price from CoinGecko API"""
        try:
            coin_id = self.symbol_mapping.get(symbol.lower(), symbol.lower())
            
            # For crypto-to-crypto pairs
            if vs_currency.lower() in self.crypto_currencies:
                vs_coin_id = self.symbol_mapping.get(vs_currency.lower(), vs_currency.lower())
                
                # Get both prices in USD
                data = await self.gateway.get_simple_price(
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
                    
                    return PriceModel(
                        symbol=symbol,
                        vs_currency=vs_currency,
                        price=price,
                        volume_24h=data[coin_id].get("usd_24h_vol"),
                        price_change_24h=data[coin_id].get("usd_24h_change"),
                        last_updated=datetime.fromtimestamp(data[coin_id].get("last_updated_at", 0)),
                        fetched_at=datetime.utcnow()  # Time when we made the API request
                    )
            else:
                # For fiat pairs
                data = await self.gateway.get_simple_price(
                    ids=coin_id,
                    vs_currencies=vs_currency.lower(),
                    include_24hr_vol=True,
                    include_24hr_change=True,
                    include_last_updated_at=True
                )
                
                if coin_id in data:
                    price_data = data[coin_id]
                    return PriceModel(
                        symbol=symbol,
                        vs_currency=vs_currency,
                        price=price_data.get(vs_currency.lower(), 0),
                        volume_24h=price_data.get(f"{vs_currency.lower()}_24h_vol"),
                        price_change_24h=price_data.get(f"{vs_currency.lower()}_24h_change"),
                        last_updated=datetime.fromtimestamp(price_data.get("last_updated_at", 0)),
                        fetched_at=datetime.utcnow()  # Time when we made the API request
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}/{vs_currency}: {e}")
            raise
    
