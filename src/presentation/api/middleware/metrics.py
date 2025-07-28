import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from src.shared.monitoring import REQUEST_COUNT, REQUEST_DURATION, ACTIVE_CONNECTIONS


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Increment active connections
        ACTIVE_CONNECTIONS.inc()
        
        # Process request
        response = None
        status = "success"
        
        try:
            response = await call_next(request)
            if response.status_code >= 400:
                status = "error"
            return response
            
        except Exception as e:
            status = "error"
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
            
            # Decrement active connections
            ACTIVE_CONNECTIONS.dec()