import asyncio
import time
from typing import Dict, Any, Optional, Callable
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class CacheWarmer:
    """Предварительная загрузка и прогрев кэша для популярных запросов"""
    
    def __init__(self):
        self._popular_pairs = [
            ("eth", "usdt"),
            ("btc", "usdt"), 
            ("bnb", "usdt")
        ]
        self._warming_interval = 30  # Прогреваем каждые 30 секунд
        self._last_warm = 0
        self._warming_task: Optional[asyncio.Task] = None
        self._data_fetcher: Optional[Callable] = None
        
    def set_data_fetcher(self, fetcher: Callable):
        """Установить функцию для получения данных"""
        self._data_fetcher = fetcher
        
    async def start_warming(self):
        """Запустить фоновый прогрев кэша"""
        if self._warming_task and not self._warming_task.done():
            return
            
        self._warming_task = asyncio.create_task(self._warming_loop())
        logger.info("Cache warming started")
        
    async def stop_warming(self):
        """Остановить прогрев кэша"""
        if self._warming_task and not self._warming_task.done():
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache warming stopped")
        
    async def _warming_loop(self):
        """Основной цикл прогрева"""
        while True:
            try:
                await asyncio.sleep(self._warming_interval)
                await self._warm_popular_keys()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warming: {e}")
                await asyncio.sleep(5)  # Короткая пауза при ошибке
                
    async def _warm_popular_keys(self):
        """Прогреть популярные ключи"""
        if not self._data_fetcher:
            return
            
        current_time = time.time()
        if current_time - self._last_warm < self._warming_interval:
            return
            
        logger.debug("Starting cache warming for popular keys")
        
        tasks = []
        for symbol, vs_currency in self._popular_pairs:
            task = asyncio.create_task(self._warm_pair(symbol, vs_currency))
            tasks.append(task)
            
        # Выполняем прогрев параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Cache warming completed: {success_count}/{len(tasks)} successful")
        
        self._last_warm = current_time
        
    async def _warm_pair(self, symbol: str, vs_currency: str):
        """Прогреть конкретную пару"""
        try:
            await self._data_fetcher(symbol, vs_currency)
            logger.debug(f"Warmed cache for {symbol}/{vs_currency}")
        except Exception as e:
            logger.warning(f"Failed to warm cache for {symbol}/{vs_currency}: {e}")