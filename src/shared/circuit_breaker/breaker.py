import asyncio
from typing import Callable, Any, Optional, Dict
from datetime import datetime, timedelta
from enum import Enum
from src.shared.config import settings
from src.shared.logging import get_logger
from src.shared.monitoring import CIRCUIT_BREAKER_STATE
from src.shared.exceptions import RateLimitExceeded

logger = get_logger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.recovery_timeout = recovery_timeout or settings.circuit_breaker_recovery_timeout
        self.expected_exception = expected_exception or Exception
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED
        self._success_count = 0
        self._total_calls = 0
        
        # Update metrics
        self._update_metrics()
        
    def _update_metrics(self):
        """Update Prometheus metrics for circuit breaker state"""
        state_value = {
            CircuitState.CLOSED: 0,
            CircuitState.OPEN: 1,
            CircuitState.HALF_OPEN: 2
        }
        CIRCUIT_BREAKER_STATE.labels(service=self.name).set(state_value[self._state])
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               datetime.now() - self._last_failure_time > timedelta(seconds=self.recovery_timeout):
                logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
                self._state = CircuitState.HALF_OPEN
                self._failure_count = 0
                self._update_metrics()
        
        return self._state
    
    def call_succeeded(self):
        self._success_count += 1
        self._failure_count = 0
        if self._state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' transitioning to CLOSED")
            self._state = CircuitState.CLOSED
            self._update_metrics()
    
    def call_failed(self):
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker '{self.name}' opening after {self._failure_count} failures")
            self._state = CircuitState.OPEN
            self._update_metrics()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        self._total_calls += 1
        
        if self.state == CircuitState.OPEN:
            logger.warning(f"Circuit breaker '{self.name}' is OPEN, rejecting call")
            raise Exception(f"Circuit breaker '{self.name}' is OPEN")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
                # Handle case where result is a coroutine
                if asyncio.iscoroutine(result):
                    result = await result
                
            self.call_succeeded()
            return result
            
        except RateLimitExceeded as e:
            # Don't count rate limit as circuit breaker failure
            logger.warning(f"Rate limit hit for '{self.name}', not counting as failure")
            raise e
        except self.expected_exception as e:
            self.call_failed()
            logger.error(f"Circuit breaker '{self.name}' recorded failure: {str(e)}")
            raise e
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "total_calls": self._total_calls,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None
        }