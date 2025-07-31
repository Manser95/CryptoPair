import asyncio
import pytest
from datetime import datetime
from typing import AsyncGenerator
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from src.data_access.models.price_model import PriceModel
from src.data_access.repositories.interfaces import CacheRepository, PriceRepository
from src.presentation.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return PriceModel(
        symbol="eth",
        vs_currency="usdt",
        price=2500.50,
        volume_24h=1000000.0,
        price_change_24h=5.25,
        last_updated=datetime.utcnow()
    )


@pytest.fixture
def mock_cache_repository():
    """Mock cache repository for testing"""
    cache_repo = AsyncMock(spec=CacheRepository)
    cache_repo.get.return_value = None
    cache_repo.set.return_value = None
    cache_repo.delete.return_value = None
    return cache_repo


@pytest.fixture
def mock_price_repository():
    """Mock price repository for testing"""
    repository = AsyncMock(spec=PriceRepository)
    return repository


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def coingecko_response():
    """Sample CoinGecko API response"""
    return {
        "ethereum": {
            "usd": 2500.50,
            "usd_24h_vol": 1000000.0,
            "usd_24h_change": 5.25,
            "last_updated_at": 1641234567
        }
    }


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker for testing"""
    breaker = MagicMock()
    breaker.call = AsyncMock(side_effect=lambda func: func())
    breaker.state = "closed"
    return breaker