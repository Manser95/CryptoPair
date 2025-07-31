from typing import Optional
import asyncio
from src.data_access.models.price_model import PriceModel
from src.data_access.repositories.interfaces import IPriceRepository, ICacheRepository
from src.data_access.repositories.redis_cache_repository import RedisCacheRepository
from src.data_access.external.coingecko_gateway import CoinGeckoGateway
from src.shared.config import settings
from src.shared.logging import get_logger
from src.shared.monitoring import track_service_metrics

logger = get_logger(__name__)


class PriceService:
    """
    Service layer for cryptocurrency price operations.
    Handles business logic, caching, and orchestration with Redis-based distributed locking.
    """
    
    def __init__(
        self,
        price_repository: IPriceRepository,
        cache_repository: ICacheRepository,
        gateway: Optional[CoinGeckoGateway] = None
    ):
        """
        Initialize price service.
        
        Args:
            price_repository: Repository for price data
            cache_repository: Repository for cache operations
            gateway: CoinGecko gateway (will create singleton if not provided)
        """
        self.price_repository = price_repository
        self.cache_repository = cache_repository
        self.gateway = gateway or CoinGeckoGateway()
        
        # Cache configuration
        self.cache_ttl = settings.cache_ttl  # From CACHE_TTL env var, default 5s
        # Disable stale-while-revalidate for fresh data requirements
        self.stale_ttl = self.cache_ttl  # Same as cache_ttl, no stale data
        
    
    @track_service_metrics(service="price_service", operation="get_current_price")
    async def get_current_price(
        self,
        symbol: str,
        vs_currency: str,
        use_cache: bool = True
    ) -> Optional[PriceModel]:
        """
        Get current price for a cryptocurrency pair with Redis-based distributed locking.
        
        Args:
            symbol: Cryptocurrency symbol (e.g., "btc", "eth")
            vs_currency: Target currency (e.g., "usd", "usdt")
            use_cache: Whether to use cache
            
        Returns:
            PriceModel or None if not found
        """
        cache_key = f"price:{symbol.lower()}:{vs_currency.lower()}"
        
        # Try cache first
        if use_cache:
            cached_entry = await self.cache_repository.get(cache_key)
            if cached_entry:
                # Check if still fresh
                if cached_entry.age_seconds < self.cache_ttl:
                    return PriceModel.from_dict(cached_entry.value)
                
                # Stale-while-revalidate
                if cached_entry.age_seconds < self.stale_ttl:
                    # Return stale data without background refresh
                    return PriceModel.from_dict(cached_entry.value)
        
        # Try to acquire distributed lock through Redis
        lock_key = f"fetch:{symbol.lower()}:{vs_currency.lower()}"
        lock_acquired = False
        
        # Check if we have Redis repository with lock support
        if isinstance(self.cache_repository, RedisCacheRepository):
            try:
                lock_acquired = await self.cache_repository.acquire_lock(
                    lock_key, 
                    lock_timeout=10,
                    acquire_timeout=5.0
                )
                
                if not lock_acquired:
                    # Another worker is fetching, wait and check cache again
                    
                    # Poll cache for up to 5 seconds
                    for _ in range(10):
                        await asyncio.sleep(0.5)
                        cached_entry = await self.cache_repository.get(cache_key)
                        if cached_entry and cached_entry.age_seconds < self.cache_ttl:
                            return PriceModel.from_dict(cached_entry.value)
                    
                    # If still nothing, proceed with our own request
                    logger.warning(f"Lock timeout for {symbol}/{vs_currency}, proceeding with own request")
                    
            except Exception as e:
                logger.error(f"Error with distributed lock for {symbol}/{vs_currency}: {e}")
                # Continue without lock in case of error
        
        try:
            # Fetch from repository
            price = await self.price_repository.get_current_price(symbol, vs_currency)
            
            if price:
                # Cache the result
                await self.cache_repository.set(
                    cache_key,
                    price.to_dict(),
                    ttl=self.cache_ttl
                )
            
            return price
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}/{vs_currency}: {e}")
            
            # Try to return stale cache on error
            if use_cache:
                cached_entry = await self.cache_repository.get(cache_key)
                if cached_entry:
                    logger.warning(f"Returning stale cache due to error for {symbol}/{vs_currency}")
                    return PriceModel.from_dict(cached_entry.value)
            
            raise
        finally:
            # Release distributed lock if we acquired it
            if lock_acquired and isinstance(self.cache_repository, RedisCacheRepository):
                try:
                    await self.cache_repository.release_lock(lock_key)
                except Exception as e:
                    logger.error(f"Error releasing lock for {symbol}/{vs_currency}: {e}")
    
    
    
    
    async def get_service_stats(self) -> dict:
        """Get service statistics"""
        cache_stats = await self.cache_repository.get_stats() if hasattr(self.cache_repository, 'get_stats') else {}
        gateway_stats = self.gateway.get_stats()
        
        return {
            "cache": cache_stats,
            "gateway": gateway_stats
        }


