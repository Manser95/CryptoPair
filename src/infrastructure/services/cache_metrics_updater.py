import asyncio
from src.shared.monitoring import CACHE_HITS, CACHE_MISSES, CACHE_HIT_RATE
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CacheMetricsUpdater:
    """Background task to update cache hit rate gauge"""
    
    def __init__(self):
        self.running = False
        self.task = None
        
    async def start(self):
        """Start the metrics updater background task"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._update_metrics())
            logger.info("Cache metrics updater started")
    
    async def stop(self):
        """Stop the metrics updater"""
        self.running = False
        if self.task:
            await self.task
            logger.info("Cache metrics updater stopped")
    
    async def _update_metrics(self):
        """Update cache hit rate metric periodically"""
        while self.running:
            try:
                # Calculate hit rate
                hits = 0
                misses = 0
                
                # Sum all cache hits and misses
                for sample in CACHE_HITS.collect()[0].samples:
                    hits += sample.value
                
                for sample in CACHE_MISSES.collect()[0].samples:
                    misses += sample.value
                
                total = hits + misses
                if total > 0:
                    hit_rate = (hits / total) * 100
                    CACHE_HIT_RATE.set(hit_rate)
                    logger.debug(f"Cache hit rate: {hit_rate:.2f}%")
                
            except Exception as e:
                logger.error(f"Error updating cache metrics: {e}")
            
            # Update every 10 seconds
            await asyncio.sleep(10)


# Global instance
cache_metrics_updater = CacheMetricsUpdater()