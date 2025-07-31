from abc import ABC, abstractmethod
from typing import Optional
from src.data_access.models.price_model import PriceModel
from src.data_access.models.cache_model import CacheEntry


class IPriceRepository(ABC):
    """Interface for price data repository"""
    
    @abstractmethod
    async def get_current_price(self, symbol: str, vs_currency: str) -> Optional[PriceModel]:
        """Get current price for a cryptocurrency pair"""
        pass
    


class ICacheRepository(ABC):
    """Interface for cache repository"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL"""
        pass
    
    @abstractmethod
    async def set_if_not_exists(self, key: str, value: any, ttl: Optional[int] = None) -> bool:
        """Set value only if key doesn't exist. Returns True if set, False if already exists"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries"""
        pass