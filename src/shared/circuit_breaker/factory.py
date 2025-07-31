"""
Factory for creating Circuit Breakers based on configuration
"""
from typing import Optional, Dict, Any
from src.shared.circuit_breaker.breaker import CircuitBreaker
from src.shared.config import settings


class CircuitBreakerFactory:
    """Factory to create appropriate Circuit Breaker instances"""
    
    _instances: Dict[str, CircuitBreaker] = {}
    
    @classmethod
    def create(
        cls,
        name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        expected_exception: type = Exception,
        persistent: bool = False,
        **kwargs
    ) -> CircuitBreaker:
        """
        Create or get existing Circuit Breaker instance
        
        Args:
            name: Unique name for the circuit breaker
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
            persistent: Whether to use persistent storage
            **kwargs: Additional arguments for specific implementations
        
        Returns:
            CircuitBreaker instance
        """
        # Return existing instance if available
        if name in cls._instances:
            return cls._instances[name]
        
        # Create new instance
        breaker = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        
        cls._instances[name] = breaker
        return breaker
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {
            name: breaker.get_stats()
            for name, breaker in cls._instances.items()
        }
    
    @classmethod
    def reset_all(cls):
        """Reset all circuit breakers (useful for testing)"""
        for breaker in cls._instances.values():
            if hasattr(breaker, 'reset'):
                breaker.reset()
    
    @classmethod
    def clear(cls):
        """Clear all instances (useful for testing)"""
        cls._instances.clear()