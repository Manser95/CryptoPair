from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CryptoPrice:
    symbol: str
    vs_currency: str
    price: float
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    last_updated: Optional[datetime] = None
    
    @property
    def pair_name(self) -> str:
        return f"{self.symbol.upper()}/{self.vs_currency.upper()}"
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "vs_currency": self.vs_currency,
            "price": self.price,
            "volume_24h": self.volume_24h,
            "price_change_24h": self.price_change_24h,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "pair": self.pair_name
        }