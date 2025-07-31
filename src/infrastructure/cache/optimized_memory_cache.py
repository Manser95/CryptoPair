from typing import Optional, Any, Dict, Callable
from cachetools import TTLCache
import asyncio
import time
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


class OptimizedMemoryCache:
    """Оптимизированный in-memory L1 cache со stale-while-revalidate паттерном"""
    
    def __init__(self, ttl: Optional[int] = None, maxsize: int = 50000):
        self.ttl = ttl or settings.cache_ttl_l1
        self.cache = TTLCache(maxsize=maxsize, ttl=self.ttl)
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}  # Метаданные кэша
        self._warming_cache: Dict[str, Any] = {}
        self._last_warming = 0
        self._warming_interval = 60  # Обновляем популярные ключи каждую минуту
        self._background_updates: Dict[str, asyncio.Task] = {}  # Фоновые обновления
        self._stale_threshold = 4  # Через 4 секунды начинаем фоновое обновление (80% от TTL)
        
    async def get(self, key: str, refresh_func: Optional[Callable] = None) -> Optional[Any]:
        """Получить значение из кэша со stale-while-revalidate паттерном"""
        value = self.cache.get(key)
        
        if value is not None:
            # Убираем debug логи для производительности
            
            # Проверяем, нужно ли фоновое обновление
            metadata = self._cache_metadata.get(key, {})
            creation_time = metadata.get('created_at', 0)
            current_time = time.time()
            
            # Если данные старше порога и есть функция обновления - запускаем фоновое обновление
            if (current_time - creation_time > self._stale_threshold and 
                refresh_func and 
                key not in self._background_updates):
                
                self._background_updates[key] = asyncio.create_task(
                    self._background_refresh(key, refresh_func)
                )
            
            return value
        else:
            logger.debug(f"L1 cache miss for key: {key}")
            return None
    
    async def set(self, key: str, value: Any) -> None:
        """Установить значение в кэш"""
        current_time = time.time()
        self.cache[key] = value
        self._cache_metadata[key] = {
            'created_at': current_time,
            'access_count': self._cache_metadata.get(key, {}).get('access_count', 0) + 1
        }
        logger.debug(f"L1 cache set for key: {key}")
        
        # Добавляем в warming cache для популярных ключей
        if key.startswith("eth-usdt") or key.startswith("btc-usdt"):
            self._warming_cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Удалить значение из кэша"""
        self.cache.pop(key, None)
        self._cache_metadata.pop(key, None)
        self._warming_cache.pop(key, None)
        
        # Отменяем фоновое обновление если оно идет
        if key in self._background_updates:
            self._background_updates[key].cancel()
            del self._background_updates[key]
            
        logger.debug(f"L1 cache delete for key: {key}")
    
    async def clear(self) -> None:
        """Очистить кэш"""
        # Отменяем все фоновые обновления
        for task in self._background_updates.values():
            task.cancel()
        self._background_updates.clear()
        
        self.cache.clear()
        self._cache_metadata.clear()
        self._warming_cache.clear()
        logger.info("L1 cache cleared")
    
    async def _maybe_warm_cache(self, key: str) -> None:
        """Предварительная загрузка популярных ключей"""
        current_time = time.time()
        if current_time - self._last_warming > self._warming_interval:
            self._last_warming = current_time
            # Продлеваем TTL для популярных ключей
            if key in self._warming_cache:
                self.cache[key] = self._warming_cache[key]
                logger.debug(f"Warmed cache for popular key: {key}")
    
    async def _background_refresh(self, key: str, refresh_func: Callable):
        """Фоновое обновление устаревших данных"""
        from src.shared.monitoring import CACHE_REFRESH_TIME
        start_time = time.time()
        
        try:
            # refresh_func уже связана с правильными параметрами
            fresh_data = await refresh_func()
            if fresh_data:
                await self.set(key, fresh_data)
                logger.debug(f"Background refresh completed for key: {key}")
                
            # Record refresh time
            refresh_time = time.time() - start_time
            CACHE_REFRESH_TIME.labels(cache_level="L1").observe(refresh_time)
        except Exception as e:
            logger.warning(f"Background refresh failed for key {key}: {e}")
        finally:
            # Удаляем задачу из активных
            self._background_updates.pop(key, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику кэша"""
        return {
            "cache_size": len(self.cache),
            "max_size": self.cache.maxsize,
            "ttl": self.ttl,
            "warming_cache_size": len(self._warming_cache),
            "metadata_entries": len(self._cache_metadata),
            "background_updates": len(self._background_updates)
        }