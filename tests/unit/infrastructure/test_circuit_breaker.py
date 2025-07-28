import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from src.infrastructure.circuit_breaker.breaker import CircuitBreaker, CircuitState


@pytest.mark.asyncio
class TestCircuitBreaker:
    """Test cases for CircuitBreaker"""
    
    def test_initialization_with_defaults(self):
        """Test CircuitBreaker initialization with default values"""
        with patch('src.infrastructure.circuit_breaker.breaker.settings') as mock_settings:
            mock_settings.circuit_breaker_failure_threshold = 5
            mock_settings.circuit_breaker_recovery_timeout = 60
            
            breaker = CircuitBreaker(name="test")
            assert breaker.name == "test"
            assert breaker.failure_threshold == 5
            assert breaker.recovery_timeout == 60
            assert breaker.expected_exception == Exception
            assert breaker._state == CircuitState.CLOSED
            assert breaker._failure_count == 0
    
    def test_initialization_with_custom_values(self):
        """Test CircuitBreaker initialization with custom values"""
        breaker = CircuitBreaker(
            name="custom",
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=ValueError
        )
        assert breaker.name == "custom"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30
        assert breaker.expected_exception == ValueError
    
    def test_state_property_when_closed(self):
        """Test state property returns CLOSED when circuit is closed"""
        breaker = CircuitBreaker(name="test")
        assert breaker.state == CircuitState.CLOSED
    
    def test_state_transition_to_half_open(self):
        """Test state transitions from OPEN to HALF_OPEN after recovery timeout"""
        breaker = CircuitBreaker(name="test", recovery_timeout=1)
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = datetime.now() - timedelta(seconds=2)
        
        # Should transition to HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN
        assert breaker._failure_count == 0
    
    def test_state_remains_open_before_recovery_timeout(self):
        """Test state remains OPEN before recovery timeout"""
        breaker = CircuitBreaker(name="test", recovery_timeout=60)
        breaker._state = CircuitState.OPEN
        breaker._last_failure_time = datetime.now()
        
        # Should remain OPEN
        assert breaker.state == CircuitState.OPEN
    
    def test_call_succeeded_resets_failure_count(self):
        """Test call_succeeded resets failure count"""
        breaker = CircuitBreaker(name="test")
        breaker._failure_count = 3
        
        breaker.call_succeeded()
        assert breaker._failure_count == 0
    
    def test_call_succeeded_closes_half_open_circuit(self):
        """Test call_succeeded transitions from HALF_OPEN to CLOSED"""
        breaker = CircuitBreaker(name="test")
        breaker._state = CircuitState.HALF_OPEN
        
        breaker.call_succeeded()
        assert breaker._state == CircuitState.CLOSED
    
    def test_call_failed_increments_failure_count(self):
        """Test call_failed increments failure count"""
        breaker = CircuitBreaker(name="test")
        assert breaker._failure_count == 0
        
        breaker.call_failed()
        assert breaker._failure_count == 1
        assert breaker._last_failure_time is not None
    
    def test_call_failed_opens_circuit_at_threshold(self):
        """Test circuit opens when failure threshold is reached"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        
        # First two failures
        breaker.call_failed()
        breaker.call_failed()
        assert breaker._state == CircuitState.CLOSED
        
        # Third failure should open circuit
        breaker.call_failed()
        assert breaker._state == CircuitState.OPEN
        assert breaker._failure_count == 3
    
    async def test_call_with_async_function_success(self):
        """Test successful async function call"""
        breaker = CircuitBreaker(name="test")
        
        async def async_func():
            return "success"
        
        result = await breaker.call(async_func)
        assert result == "success"
        assert breaker._failure_count == 0
    
    async def test_call_with_sync_function_success(self):
        """Test successful sync function call"""
        breaker = CircuitBreaker(name="test")
        
        def sync_func():
            return "success"
        
        result = await breaker.call(sync_func)
        assert result == "success"
        assert breaker._failure_count == 0
    
    async def test_call_with_async_function_failure(self):
        """Test async function call that raises expected exception"""
        breaker = CircuitBreaker(name="test", expected_exception=ValueError)
        
        async def async_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            await breaker.call(async_func)
        
        assert breaker._failure_count == 1
    
    async def test_call_when_circuit_is_open(self):
        """Test call raises exception when circuit is open"""
        breaker = CircuitBreaker(name="test")
        breaker._state = CircuitState.OPEN
        
        async def async_func():
            return "should not be called"
        
        with pytest.raises(Exception) as exc_info:
            await breaker.call(async_func)
        
        assert "Circuit breaker" in str(exc_info.value) and "is OPEN" in str(exc_info.value)
    
    async def test_call_with_arguments(self):
        """Test call passes arguments correctly"""
        breaker = CircuitBreaker(name="test")
        
        async def async_func(a, b, c=None):
            return f"{a}-{b}-{c}"
        
        result = await breaker.call(async_func, "arg1", "arg2", c="arg3")
        assert result == "arg1-arg2-arg3"
    
    async def test_circuit_breaker_flow(self):
        """Test complete circuit breaker flow"""
        breaker = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=1)
        
        async def failing_func():
            raise Exception("fail")
        
        async def success_func():
            return "success"
        
        # Initial state is CLOSED
        assert breaker.state == CircuitState.CLOSED
        
        # First failure
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        assert breaker._failure_count == 1
        assert breaker.state == CircuitState.CLOSED
        
        # Second failure - circuit opens
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        assert breaker._failure_count == 2
        assert breaker._state == CircuitState.OPEN
        
        # Call while OPEN fails immediately
        with pytest.raises(Exception) as exc_info:
            await breaker.call(success_func)
        assert "Circuit breaker" in str(exc_info.value) and "is OPEN" in str(exc_info.value)
        
        # Wait for recovery timeout
        await asyncio.sleep(1.1)
        
        # Circuit should be HALF_OPEN now
        assert breaker.state == CircuitState.HALF_OPEN
        
        # Successful call closes circuit
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0