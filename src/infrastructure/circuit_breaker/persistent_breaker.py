"""
Persistent Circuit Breaker implementation that saves state to disk.
Useful for maintaining state across application restarts.
"""
import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from src.infrastructure.circuit_breaker.breaker import CircuitBreaker, CircuitState
from src.shared.logging import get_logger

logger = get_logger(__name__)


class PersistentCircuitBreaker(CircuitBreaker):
    """Circuit Breaker with file-based persistence"""
    
    def __init__(
        self,
        name: str,
        failure_threshold: Optional[int] = None,
        recovery_timeout: Optional[int] = None,
        expected_exception: type = Exception,
        state_dir: str = "/tmp/circuit_breakers"
    ):
        super().__init__(name, failure_threshold, recovery_timeout, expected_exception)
        
        self.state_dir = Path(state_dir)
        self.state_file = self.state_dir / f"{name}_state.json"
        
        # Create state directory if it doesn't exist
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # Load persisted state
        self._load_state()
    
    def _load_state(self):
        """Load state from disk if available"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                self._state = CircuitState(data['state'])
                self._failure_count = data['failure_count']
                self._success_count = data['success_count']
                self._total_calls = data['total_calls']
                
                if data['last_failure_time']:
                    self._last_failure_time = datetime.fromisoformat(data['last_failure_time'])
                
                logger.info(f"Loaded circuit breaker '{self.name}' state: {self._state.value}")
                self._update_metrics()
        except Exception as e:
            logger.error(f"Failed to load circuit breaker state for '{self.name}': {e}")
    
    def _save_state(self):
        """Persist current state to disk"""
        try:
            state_data = {
                'state': self._state.value,
                'failure_count': self._failure_count,
                'success_count': self._success_count,
                'total_calls': self._total_calls,
                'last_failure_time': self._last_failure_time.isoformat() if self._last_failure_time else None,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save circuit breaker state for '{self.name}': {e}")
    
    def call_succeeded(self):
        """Override to save state after success"""
        super().call_succeeded()
        self._save_state()
    
    def call_failed(self):
        """Override to save state after failure"""
        super().call_failed()
        self._save_state()
    
    def reset(self):
        """Reset circuit breaker and clear persisted state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._update_metrics()
        
        # Remove state file
        if self.state_file.exists():
            self.state_file.unlink()
            
        logger.info(f"Circuit breaker '{self.name}' has been reset")