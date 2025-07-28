import asyncio
import random
from typing import TypeVar, Callable, Optional, Union, Type
from functools import wraps
from src.shared.config import settings
from src.shared.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def exponential_backoff_retry(
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    max_delay: float = 60.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    jitter: bool = True
):
    """
    Decorator for retry with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exceptions: Exception types to catch
        jitter: Add random jitter to delays
    """
    max_attempts = max_attempts or settings.retry_max_attempts
    base_delay = base_delay or settings.retry_wait_fixed
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    if jitter:
                        jitter_range = delay * 0.1
                        delay += random.uniform(-jitter_range, jitter_range)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s. Error: {e}"
                    )
                    
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    if jitter:
                        jitter_range = delay * 0.1
                        delay += random.uniform(-jitter_range, jitter_range)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s. Error: {e}"
                    )
                    
                    asyncio.run(asyncio.sleep(delay))
            
            raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator