from typing import Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Model for cache entries"""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    hit_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def age_seconds(self) -> float:
        return (datetime.utcnow() - self.created_at).total_seconds()