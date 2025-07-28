from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.shared.config import settings
from src.shared.logging import setup_logging
from src.shared.monitoring import get_metrics
from src.presentation.api.middleware.correlation import CorrelationIdMiddleware
from src.presentation.api.middleware.metrics import MetricsMiddleware
from src.presentation.api.routers import prices, health
from src.presentation.api.dependencies import get_coingecko_client
from src.infrastructure.services.cache_metrics_updater import cache_metrics_updater
from src.shared.metrics_initializer import initialize_metrics

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Crypto Pairs API")
    
    # Initialize metrics
    initialize_metrics()
    logger.info("Metrics initialized")
    
    # Start background tasks
    await cache_metrics_updater.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Crypto Pairs API")
    
    # Stop background tasks
    await cache_metrics_updater.stop()
    
    # Cleanup connections
    client = await get_coingecko_client()
    await client.close()


app = FastAPI(
    title=settings.app_name,
    description="High-performance cryptocurrency pairs tracking service",
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

# Include routers
app.include_router(health.router)
app.include_router(prices.router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    return {
        "message": "Crypto Pairs API",
        "version": settings.app_version,
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check for compatibility"""
    return {"status": "healthy", "message": "Use /health/liveness or /health/readiness"}


@app.get(settings.metrics_path, include_in_schema=False)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics(), media_type="text/plain")