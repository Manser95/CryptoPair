import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import logging


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        
        # Add correlation ID to request state
        request.state.correlation_id = correlation_id
        
        # Add to logging context
        logging.LoggerAdapter(logging.getLogger(), {"correlation_id": correlation_id})
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response