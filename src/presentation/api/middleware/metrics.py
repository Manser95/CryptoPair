import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from prometheus_client import Counter, Histogram, Gauge
from src.shared.monitoring import REQUEST_COUNT, REQUEST_DURATION, ACTIVE_CONNECTIONS


# Additional metrics
REQUEST_SIZE = Histogram(
    'fastapi_request_size_bytes',
    'Request size in bytes',
    ['method', 'endpoint']
)

RESPONSE_SIZE = Histogram(
    'fastapi_response_size_bytes',
    'Response size in bytes',
    ['method', 'endpoint']
)

REQUEST_COUNT_BY_STATUS = Counter(
    'fastapi_requests_total',
    'Total requests by status code',
    ['method', 'path', 'status']
)

REQUEST_DURATION_HISTOGRAM = Histogram(
    'fastapi_request_duration_seconds',
    'Request duration histogram',
    ['method', 'path', 'status'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

IN_PROGRESS = Gauge(
    'fastapi_inprogress',
    'Number of requests in progress'
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active connections and in-progress requests
        ACTIVE_CONNECTIONS.inc()
        IN_PROGRESS.inc()
        
        # Record request size
        content_length = request.headers.get('content-length')
        if content_length:
            REQUEST_SIZE.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(int(content_length))
        
        # Process request
        response = None
        status = "success"
        status_code = 200
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            if response.status_code >= 400:
                status = "error"
            
            # Record response size
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                RESPONSE_SIZE.labels(
                    method=request.method,
                    endpoint=request.url.path
                ).observe(int(response.headers['content-length']))
            
            return response
            
        except Exception as e:
            status = "error"
            status_code = 500
            raise
            
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status
            ).inc()
            
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            REQUEST_COUNT_BY_STATUS.labels(
                method=request.method,
                path=request.url.path,
                status=str(status_code)
            ).inc()
            
            REQUEST_DURATION_HISTOGRAM.labels(
                method=request.method,
                path=request.url.path,
                status=str(status_code)
            ).observe(duration)
            
            # Decrement active connections and in-progress requests
            ACTIVE_CONNECTIONS.dec()
            IN_PROGRESS.dec()