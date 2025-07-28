from typing import Optional
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
    
    async def execute(self, symbol: str, vs_currency: str) -> Optional[CryptoPrice]:
        """Get current price for a cryptocurrency pair with stale-while-revalidate"""
        cache_key = f"price:{symbol}:{vs_currency}"
        
        # Создаем функцию для фонового обновления
        async def refresh_func(sym: str, vs_cur: str) -> Optional[dict]:
            fresh_price = await self.price_repository.get_current_price(sym, vs_cur)
            return fresh_price.to_dict() if fresh_price else None
        
        # Try to get from cache first with stale-while-revalidate
        cached_data = await self.cache_service.get(cache_key, refresh_func)
        if cached_data:
            logger.info(f"Returning cached price for {symbol}/{vs_currency}")
            # Remove 'pair' field from cached data as it's not in the CryptoPrice constructor
            cached_data.pop('pair', None)
            # Convert last_updated string back to datetime if present
            if cached_data.get('last_updated') and isinstance(cached_data['last_updated'], str):
                from datetime import datetime
                cached_data['last_updated'] = datetime.fromisoformat(cached_data['last_updated'])
            return CryptoPrice(**cached_data)
        
        # Get from repository if not in cache
        price = await self.price_repository.get_current_price(symbol, vs_currency)
        
        if price:
            # Cache the result
            await self.cache_service.set(cache_key, price.to_dict())
            logger.info(f"Fetched and cached price for {symbol}/{vs_currency}")
        
        return price