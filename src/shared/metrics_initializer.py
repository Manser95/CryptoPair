"""Initialize Prometheus metrics with default values to ensure they appear in /metrics endpoint"""
from src.shared.monitoring import (
    REQUEST_COUNT, REQUEST_DURATION, CACHE_HITS, CACHE_MISSES, 
    EXTERNAL_API_REQUESTS, EXTERNAL_API_DURATION, CIRCUIT_BREAKER_STATE,
    ACTIVE_CONNECTIONS, CACHE_HIT_RATE
)
from src.presentation.api.middleware.metrics import (
    REQUEST_SIZE, RESPONSE_SIZE, REQUEST_COUNT_BY_STATUS, 
    REQUEST_DURATION_HISTOGRAM, IN_PROGRESS
)


def initialize_metrics():
    """Initialize all metrics with default values so they appear in Prometheus"""
    # Request metrics - use inc() with 0 to initialize counters
    REQUEST_COUNT.labels(method="GET", endpoint="/health", status="success").inc(0)
    REQUEST_DURATION.labels(method="GET", endpoint="/health").observe(0)
    
    # FastAPI specific metrics
    REQUEST_COUNT_BY_STATUS.labels(method="GET", path="/health", status="200").inc(0)
    REQUEST_DURATION_HISTOGRAM.labels(method="GET", path="/health", status="200").observe(0)
    REQUEST_SIZE.labels(method="GET", endpoint="/health").observe(0)
    RESPONSE_SIZE.labels(method="GET", endpoint="/health").observe(0)
    
    # Cache metrics
    CACHE_HITS.labels(cache_level="memory", operation="get").inc(0)
    CACHE_MISSES.labels(cache_level="memory", operation="get").inc(0)
    CACHE_HIT_RATE.labels(cache_level="memory").set(0)
    
    # External API metrics
    EXTERNAL_API_REQUESTS.labels(api="coingecko", endpoint="/simple/price", status="success").inc(0)
    EXTERNAL_API_DURATION.labels(api="coingecko", endpoint="/simple/price").observe(0)
    
    # Circuit breaker
    CIRCUIT_BREAKER_STATE.labels(service="coingecko").set(0)
    
    # Gauges
    ACTIVE_CONNECTIONS.set(0)
    IN_PROGRESS.set(0)