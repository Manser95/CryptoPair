from typing import Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PriceModel:
    """Data model for cryptocurrency price information"""
    symbol: str
    vs_currency: str
    price: float
    volume_24h: Optional[float] = None
    price_change_24h: Optional[float] = None
    last_updated: Optional[datetime] = None  # When CoinGecko last updated the data
    fetched_at: Optional[datetime] = None    # When we fetched the data from API
    
    def to_dict(self) -> dict:
        return {
            'symbol': self.symbol,
            'vs_currency': self.vs_currency,
            'price': self.price,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'fetched_at': self.fetched_at.isoformat() if self.fetched_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PriceModel':
        return cls(
            symbol=data['symbol'],
            vs_currency=data['vs_currency'],
            price=data['price'],
            volume_24h=data.get('volume_24h'),
            price_change_24h=data.get('price_change_24h'),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else None,
            fetched_at=datetime.fromisoformat(data['fetched_at']) if data.get('fetched_at') else None
        )