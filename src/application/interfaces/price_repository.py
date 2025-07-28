from abc import ABC, abstractmethod
from typing import Optional
from src.domain.entities.crypto_price import CryptoPrice


class PriceRepositoryInterface(ABC):
    @abstractmethod
    async def get_current_price(self, symbol: str, vs_currency: str) -> Optional[CryptoPrice]:
        """Get current price for a cryptocurrency pair"""
        pass
    
    @abstractmethod
    async def get_price_history(self, symbol: str, vs_currency: str, days: int) -> list:
        """Get price history for a cryptocurrency pair"""
        pass