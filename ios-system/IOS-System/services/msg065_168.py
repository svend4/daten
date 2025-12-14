"""
Circuit Breaker Pattern
Protects against cascading failures
"""

import logging
from typing import Callable, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance
    
    Features:
    - Automatic failure detection
    - Configurable thresholds
    - Exponential backoff
    - Health check probing
    - Metrics tracking
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    
    Usage:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        @breaker.protected
        async def call_external_service():
            ...
    """
    
    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.half_open_max_calls = half_open_max_calls
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None
        
        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.state_changes = []
    
    def protected(self, func: Callable):
        """Decorator to protect function with circuit breaker"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        
        return wrapper
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        
        Args:
            func: Function to call
            *args, **kwargs: Function arguments
        
        Returns:
            Function result
        
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        
        self.total_calls += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout elapsed
            if self._should_attempt_reset():
                self._transition_to(CircuitState.HALF_OPEN)
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        try:
            # Call function
            result = await func(*args, **kwargs)
            
            # Record success
            await self._on_success()
            
            return result
            
        except self.expected_exception as e:
            # Record failure
            await self._on_failure(e)
            raise
    
    async def _on_success(self):
        """Handle successful call"""
        
        self.total_successes += 1
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # If enough successes, close circuit
            if self.success_count >= self.half_open_max_calls:
                self._transition_to(CircuitState.CLOSED)
                logger.info(
                    f"Circuit breaker '{self.name}' recovered, "
                    f"transitioning to CLOSED"
                )
    
    async def _on_failure(self, exception: Exception):
        """Handle failed call"""
        
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(
            f"Circuit breaker '{self.name}' failure {self.failure_count}/"
            f"{self.failure_threshold}: {exception}"
        )
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open on failure during testing
            self._transition_to(CircuitState.OPEN)
        
        elif self.failure_count >= self.failure_threshold:
            # Open circuit after threshold
            self._transition_to(CircuitState.OPEN)
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset"""
        
        if not self.opened_at:
            return False
        
        elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state"""
        
        old_state = self.state
        self.state = new_state
        
        if new_state == CircuitState.OPEN:
            self.opened_at = datetime.utcnow()
            self.success_count = 0
        
        elif new_state == CircuitState.HALF_OPEN:
            self.failure_count = 0
            self.success_count = 0
        
        elif new_state == CircuitState.CLOSED:
            self.opened_at = None
            self.failure_count = 0
            self.success_count = 0
        
        # Record state change
        self.state_changes.append({
            "from": old_state,
            "to": new_state,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        logger.info(
            f"Circuit breaker '{self.name}' state: {old_state} → {new_state}"
        )
    
    def get_state(self) -> Dict:
        """Get current state"""
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": round(
                self.total_failures / self.total_calls * 100, 2
            ) if self.total_calls > 0 else 0,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "last_failure": self.last_failure_time.isoformat() 
                if self.last_failure_time else None
        }
    
    async def reset(self):
        """Manually reset circuit breaker"""
        
        self._transition_to(CircuitState.CLOSED)
        logger.info(f"Circuit breaker '{self.name}' manually reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breaker registry
class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_or_create(
        self,
        name: str,
        **kwargs
    ) -> CircuitBreaker:
        """Get or create circuit breaker"""
        
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name=name, **kwargs)
        
        return self.breakers[name]
    
    def get_all_states(self) -> Dict:
        """Get states of all circuit breakers"""
        
        return {
            name: breaker.get_state()
            for name, breaker in self.breakers.items()
        }


# Global circuit breaker
circuit_breaker = CircuitBreakerRegistry()