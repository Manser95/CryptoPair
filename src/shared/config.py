from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Application
    app_name: str = Field(default="Crypto Pairs API")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    
    # API
    api_v1_prefix: str = Field(default="/api/v1")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379")
    redis_decode_responses: bool = Field(default=True)
    
    # Cache TTL
    cache_ttl_l1: int = Field(default=5, description="L1 memory cache TTL in seconds")
    cache_ttl_l2: int = Field(default=300, description="L2 Redis cache TTL in seconds")
    
    # CoinGecko API
    coingecko_api_key: Optional[str] = Field(default=None)
    coingecko_base_url: str = Field(default="https://api.coingecko.com/api/v3")
    coingecko_timeout: int = Field(default=30)
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = Field(default=5)
    circuit_breaker_recovery_timeout: int = Field(default=60)
    
    # Retry
    retry_max_attempts: int = Field(default=5)
    retry_wait_fixed: int = Field(default=4)
    retry_wait_random_min: int = Field(default=0)
    retry_wait_random_max: int = Field(default=2)
    
    # Rate limiting
    rate_limit_calls: int = Field(default=30)
    rate_limit_period: int = Field(default=60)
    
    # AIOHTTP
    aiohttp_total_connections: int = Field(default=300)
    aiohttp_connections_per_host: int = Field(default=50)
    aiohttp_dns_ttl: int = Field(default=300)
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")
    
    # Monitoring
    enable_metrics: bool = Field(default=True)
    metrics_path: str = Field(default="/metrics")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


settings = Settings()