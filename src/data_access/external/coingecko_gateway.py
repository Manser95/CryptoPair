import asyncio
from typing import Dict, Any, Callable
from datetime import datetime, timedelta
import threading
from src.data_access.external.coingecko_client import CoinGeckoClient
from src.shared.circuit_breaker.factory import CircuitBreakerFactory
from src.shared.logging import get_logger
from src.shared.config import settings

logger = get_logger(__name__)


class CoinGeckoGateway:
    """
    Singleton gateway for CoinGecko API with rate limiting and request queue.
    Ensures only 30 requests per minute are sent to the API.
    """
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
    
    def __init__(self):
        # Prevent re-initialization
        if CoinGeckoGateway._initialized:
            return
            
        CoinGeckoGateway._initialized = True
        
        # Initialize components
        self.client = CoinGeckoClient()
        self.circuit_breaker = CircuitBreakerFactory.create(
            name="coingecko_gateway",
            failure_threshold=5,
            recovery_timeout=60,
            persistent=False
        )
        
        # Rate limiting configuration from settings
        self.max_requests_per_minute = settings.rate_limit_calls
        self.request_interval = 60.0 / self.max_requests_per_minute  # seconds between requests
        
        # Request queue and processing
        self.request_queue: asyncio.Queue = None
        self.processing_task = None
        self.last_request_time = 0
        self._running = False
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "queue_size": 0,
            "average_wait_time": 0
        }
        
        # Request history for tracking rate limits
        self.request_history = []  # List of (timestamp, url) tuples
        
        logger.info("CoinGeckoGateway singleton initialized")
    
    async def start(self):
        """Start the request processing task"""
        if self.request_queue is None:
            self.request_queue = asyncio.Queue()
        
        if not self._running:
            self._running = True
            self.processing_task = asyncio.create_task(self._process_requests())
            logger.info("CoinGeckoGateway request processor started")
    
    async def stop(self):
        """Stop the request processing task"""
        self._running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        logger.info("CoinGeckoGateway request processor stopped")
    
    async def execute_request(
        self,
        method: Callable,
        priority: int = 5,
        **kwargs
    ) -> Any:
        """
        Queue a request for execution with rate limiting.
        
        Args:
            method: The method to call on the client
            priority: Request priority (1-10, lower is higher priority)
            **kwargs: Arguments to pass to the method
            
        Returns:
            The result of the API call
        """
        if not self._running:
            await self.start()
        
        # Create request container
        future = asyncio.Future()
        request = {
            "method": method,
            "kwargs": kwargs,
            "future": future,
            "priority": priority,
            "queued_at": datetime.utcnow()
        }
        
        # Add to queue
        await self.request_queue.put((priority, request))
        self.stats["queue_size"] = self.request_queue.qsize()
        
        # Wait for result
        try:
            result = await future
            return result
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def _process_requests(self):
        """Process requests from the queue with rate limiting"""
        logger.info("Starting request processor")
        
        while self._running:
            try:
                # Get next request (blocks if queue is empty)
                _, request = await self.request_queue.get()
                
                # Calculate wait time for rate limiting
                current_time = asyncio.get_event_loop().time()
                time_since_last = current_time - self.last_request_time
                
                if time_since_last < self.request_interval:
                    wait_time = self.request_interval - time_since_last
                    await asyncio.sleep(wait_time)
                
                # Execute request through circuit breaker
                try:
                    method = request["method"]
                    kwargs = request["kwargs"]
                    
                    # Clean up old request history (older than 1 minute)
                    current_timestamp = datetime.utcnow()
                    one_minute_ago = current_timestamp - timedelta(minutes=1)
                    self.request_history = [
                        (ts, url) for ts, url in self.request_history 
                        if ts > one_minute_ago
                    ]
                    
                    # Build request URL for logging
                    request_url = f"{method.__name__}({kwargs})"
                    
                    # Count requests in last minute
                    requests_last_minute = len(self.request_history) + 1
                    
                    
                    # Execute the request
                    result = await self.circuit_breaker.call(
                        method,
                        **kwargs
                    )
                    
                    # Add to history
                    self.request_history.append((current_timestamp, request_url))
                    
                    # Update statistics
                    self.stats["total_requests"] += 1
                    self.stats["successful_requests"] += 1
                    
                    # Update wait time statistics
                    wait_time = (datetime.utcnow() - request["queued_at"]).total_seconds()
                    self.stats["average_wait_time"] = (
                        (self.stats["average_wait_time"] * (self.stats["total_requests"] - 1) + wait_time) /
                        self.stats["total_requests"]
                    )
                    
                    # Set result
                    request["future"].set_result(result)
                    
                except Exception as e:
                    self.stats["total_requests"] += 1
                    self.stats["failed_requests"] += 1
                    request["future"].set_exception(e)
                    logger.error(f"Request execution failed: {e}")
                
                # Update last request time
                self.last_request_time = asyncio.get_event_loop().time()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected error in request processor: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors
    
    async def get_simple_price(self, **kwargs) -> Dict[str, Any]:
        """Get simple price data with rate limiting"""
        return await self.execute_request(
            method=self.client.get_simple_price,
            priority=5,
            **kwargs
        )
    
    async def get_coin_market_chart(self, **kwargs) -> Dict[str, Any]:
        """Get market chart data with rate limiting"""
        return await self.execute_request(
            method=self.client.get_coin_market_chart,
            priority=7,  # Lower priority than current prices
            **kwargs
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics"""
        # Count requests in last minute
        current_time = datetime.utcnow()
        one_minute_ago = current_time - timedelta(minutes=1)
        recent_requests = [
            (ts, url) for ts, url in self.request_history 
            if ts > one_minute_ago
        ]
        
        return {
            **self.stats,
            "requests_per_minute": self.max_requests_per_minute,
            "requests_last_minute": len(recent_requests),
            "recent_requests": [
                {"time": ts.isoformat(), "request": url} 
                for ts, url in recent_requests[-10:]  # Last 10 requests
            ],
            "circuit_breaker_state": self.circuit_breaker.state,
            "is_running": self._running
        }
    
    async def close(self):
        """Close the gateway and cleanup resources"""
        await self.stop()
        await self.client.close()