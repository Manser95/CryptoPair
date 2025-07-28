import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoints:
    """Integration tests for health check endpoints"""
    
    async def test_liveness_endpoint(self, async_client: AsyncClient):
        """Test liveness endpoint returns correct response"""
        response = await async_client.get("/health/liveness")
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "alive"}
    
    async def test_readiness_endpoint(self, async_client: AsyncClient):
        """Test readiness endpoint returns correct response"""
        response = await async_client.get("/health/readiness")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["api"] == "ok"
    
    async def test_health_endpoints_no_auth_required(self, async_client: AsyncClient):
        """Test that health endpoints don't require authentication"""
        # Test without any auth headers
        liveness_response = await async_client.get("/health/liveness")
        readiness_response = await async_client.get("/health/readiness")
        
        assert liveness_response.status_code == 200
        assert readiness_response.status_code == 200
    
    async def test_health_endpoints_response_time(self, async_client: AsyncClient):
        """Test that health endpoints respond quickly"""
        import time
        
        # Liveness check should be very fast
        start_time = time.time()
        response = await async_client.get("/health/liveness")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 0.1  # Should respond in less than 100ms
        
        # Readiness check should also be fast
        start_time = time.time()
        response = await async_client.get("/health/readiness")
        elapsed_time = time.time() - start_time
        
        assert response.status_code == 200
        assert elapsed_time < 0.1  # Should respond in less than 100ms
    
    async def test_health_endpoints_content_type(self, async_client: AsyncClient):
        """Test that health endpoints return JSON content type"""
        liveness_response = await async_client.get("/health/liveness")
        readiness_response = await async_client.get("/health/readiness")
        
        assert liveness_response.headers["content-type"] == "application/json"
        assert readiness_response.headers["content-type"] == "application/json"
    
    async def test_readiness_response_structure(self, async_client: AsyncClient):
        """Test readiness endpoint response structure"""
        response = await async_client.get("/health/readiness")
        data = response.json()
        
        # Check required fields
        assert "status" in data
        assert "checks" in data
        
        # Check status values
        assert data["status"] in ["ready", "not_ready"]
        
        # Check checks structure
        assert isinstance(data["checks"], dict)
        assert "api" in data["checks"]
        assert data["checks"]["api"] in ["ok", "error"]