from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PriceResponse(BaseModel):
    symbol: str = Field(..., description="Cryptocurrency symbol")
    vs_currency: str = Field(..., description="Target currency")
    price: float = Field(..., description="Current price")
    volume_24h: Optional[float] = Field(None, description="24 hour trading volume")
    price_change_24h: Optional[float] = Field(None, description="24 hour price change percentage")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")
    pair: str = Field(..., description="Trading pair name")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")