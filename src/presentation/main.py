from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.shared.config import settings
from src.shared.logging import setup_logging
from src.shared.monitoring import get_metrics
from src.presentation.api.middleware.correlation import CorrelationIdMiddleware
from src.presentation.api.middleware.metrics import MetricsMiddleware
from src.presentation.api.v1.routes import prices, health, queue
from src.presentation.api.dependencies import startup_event, shutdown_event
from src.shared.metrics_initializer import initialize_metrics

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Crypto Pairs API with 3-layer architecture")
    
    # Initialize metrics
    initialize_metrics()
    logger.info("Metrics initialized")
    
    # Initialize all services
    await startup_event()
    logger.info("All services started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Crypto Pairs API")
    
    # Cleanup all services
    await shutdown_event()
    logger.info("All services shut down successfully")


app = FastAPI(
    title=settings.app_name,
    description="High-performance cryptocurrency pairs tracking service with rate-limited CoinGecko integration",
    version=settings.app_version,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routers
api_v1_prefix = "/api/v1"
app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(prices.router, prefix=api_v1_prefix)
app.include_router(queue.router, prefix=api_v1_prefix)


@app.get("/")
async def root():
    return {
        "message": "Crypto Pairs API",
        "version": settings.app_version,
        "docs": "/docs",
        "architecture": "3-layer (Presentation, Service, Data Access)",
        "rate_limit": "30 requests/minute to CoinGecko"
    }


@app.get("/health")
async def health():
    """Legacy health check for compatibility"""
    return {
        "status": "healthy",
        "message": "Use /api/v1/health for detailed status"
    }


@app.get(settings.metrics_path, include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics(), media_type="text/plain")