from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StatusEnum(str, Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"


class PriceResponse(BaseModel):
    """Response schema for price data"""
    symbol: str = Field(..., description="Cryptocurrency symbol")
    vs_currency: str = Field(..., description="Target currency")
    price: float = Field(..., description="Current price")
    volume_24h: Optional[float] = Field(None, description="24 hour trading volume")
    price_change_24h: Optional[float] = Field(None, description="24 hour price change percentage")
    last_updated: Optional[datetime] = Field(None, description="When CoinGecko last updated this data")
    fetched_at: Optional[datetime] = Field(None, description="When we fetched this data from CoinGecko API")
    pair: Optional[str] = Field(None, description="Trading pair format (e.g., ETH/USDT)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response schema"""
    status: StatusEnum = Field(default=StatusEnum.ERROR)
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")
    services: Dict[str, str] = Field(..., description="Status of dependent services")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueueStatusResponse(BaseModel):
    """Queue status response"""
    queue_size: int = Field(..., description="Current number of requests in queue")
    processing_rate: float = Field(..., description="Requests per minute being processed")
    average_wait_time: float = Field(..., description="Average wait time in seconds")
    rate_limit: Dict[str, Any] = Field(..., description="Rate limit information")
    circuit_breaker: str = Field(..., description="Circuit breaker status")