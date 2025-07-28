from typing import Optional
from datetime import datetime
from src.application.interfaces.price_repository import PriceRepositoryInterface
from src.application.interfaces.cache_service import CacheServiceInterface
from src.domain.entities.crypto_price import CryptoPrice
from src.shared.logging import get_logger

logger = get_logger(__name__)


class GetPriceUseCase:
    def __init__(
        self,
        price_repository: PriceRepositoryInterface,
        cache_service: CacheServiceInterface
    ):
        self.price_repository = price_repository
        self.cache_service = cache_service
    
    async def _refresh_price(self, symbol: str, vs_currency: str) -> Optional[dict]:
        """Fetch fresh price data from repository"""
        fresh_price = await self.price_repository.get_current_price(symbol, vs_currency)
        return fresh_price.to_dict() if fresh_price else None
    
    async def execute(self, symbol: str, vs_currency: str) -> Optional[CryptoPrice]:
        """Get current price for a cryptocurrency pair with stale-while-revalidate"""
        cache_key = f"price:{symbol}:{vs_currency}"
        
        # Try to get from cache first with stale-while-revalidate
        cached_data = await self.cache_service.get(cache_key, self._refresh_price)
        if cached_data:
            logger.info(f"Returning cached price for {symbol}/{vs_currency}")
            return CryptoPrice(
                symbol=cached_data['symbol'],
                vs_currency=cached_data['vs_currency'],
                price=cached_data['price'],
                volume_24h=cached_data.get('volume_24h'),
                price_change_24h=cached_data.get('price_change_24h'),
                last_updated=datetime.fromisoformat(cached_data['last_updated']) if cached_data.get('last_updated') else None
            )
        
        # Get from repository if not in cache
        price = await self.price_repository.get_current_price(symbol, vs_currency)
        
        if price:
            # Cache the result
            await self.cache_service.set(cache_key, price.to_dict())
            logger.info(f"Fetched and cached price for {symbol}/{vs_currency}")
        
        return price