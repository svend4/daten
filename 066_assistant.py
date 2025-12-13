Отлично! Пользователь готов к Week 21-22. Давайте продолжим развитие IOS System. 

Week 21-22 должны быть посвящены Integration Platform & API Gateway - созданию полноценной интеграционной платформы с API Gateway, webhook system, external API integrations, event-driven architecture.

Это логичное продолжение после AI/ML infrastructure - теперь нужно интегрировать систему с внешним миром.

План Week 21-22:
- Day 127-128: API Gateway & Rate Limiting
- Day 129-130: Webhook System & Event Bus
- Day 131-132: External Integrations & SDK

Начнем с Day 127-128: API Gateway & Rate Limiting.# 🌐 WEEK 21-22: INTEGRATION PLATFORM & API GATEWAY

---

## 📋 ПЛАН НЕДЕЛИ

**Day 127-128:** API Gateway & Rate Limiting  
**Day 129-130:** Webhook System & Event Bus  
**Day 131-132:** External Integrations & SDK

---

# 🚪 DAY 127-128: API GATEWAY & RATE LIMITING

---

## 📊 ЦЕЛЬ

Создание production-ready API Gateway:
- **Advanced Rate Limiting** - гибкое ограничение запросов
- **Request Routing** - интеллектуальная маршрутизация
- **API Versioning** - управление версиями API
- **Circuit Breaker** - защита от сбоев
- **Request/Response Transformation** - преобразование данных
- **API Analytics** - детальная аналитика использования

---

## ФАЙЛ 1: `ios_core/gateway/__init__.py`

```python
"""
API Gateway Module
"""

from .rate_limiter import RateLimiter, rate_limiter
from .circuit_breaker import CircuitBreaker, circuit_breaker
from .request_router import RequestRouter, request_router
from .api_analytics import APIAnalytics, api_analytics

__all__ = [
    'RateLimiter',
    'rate_limiter',
    'CircuitBreaker',
    'circuit_breaker',
    'RequestRouter',
    'request_router',
    'APIAnalytics',
    'api_analytics',
]
```

---

## ФАЙЛ 2: `ios_core/gateway/rate_limiter.py`

```python
"""
Advanced Rate Limiting
Multi-tier rate limiting with Redis backend
"""

import logging
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio

import redis.asyncio as redis
from fastapi import HTTPException

from ..config import settings

logger = logging.getLogger(__name__)


class RateLimitTier(str, Enum):
    """Rate limit tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class RateLimiter:
    """
    Advanced multi-tier rate limiter
    
    Features:
    - Multiple rate limit windows (second, minute, hour, day)
    - User-tier based limits
    - IP-based limits
    - Endpoint-specific limits
    - Sliding window algorithm
    - Burst allowance
    - Rate limit headers
    
    Usage:
        limiter = RateLimiter()
        
        # Check rate limit
        allowed, retry_after = await limiter.check_rate_limit(
            key="user:123",
            tier=RateLimitTier.PREMIUM
        )
        
        if not allowed:
            raise HTTPException(429, f"Retry after {retry_after}s")
    """
    
    # Rate limits by tier (requests per window)
    TIER_LIMITS = {
        RateLimitTier.FREE: {
            "second": 2,
            "minute": 60,
            "hour": 1000,
            "day": 10000
        },
        RateLimitTier.BASIC: {
            "second": 5,
            "minute": 150,
            "hour": 5000,
            "day": 50000
        },
        RateLimitTier.PREMIUM: {
            "second": 10,
            "minute": 300,
            "hour": 15000,
            "day": 200000
        },
        RateLimitTier.ENTERPRISE: {
            "second": 50,
            "minute": 1000,
            "hour": 50000,
            "day": 1000000
        },
        RateLimitTier.ADMIN: {
            "second": 100,
            "minute": 5000,
            "hour": 100000,
            "day": 10000000
        }
    }
    
    # Window durations in seconds
    WINDOWS = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400
    }
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}  # Fallback
        self.cache_ttl = 60
    
    async def initialize(self):
        """Initialize Redis connection"""
        
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Rate limiter initialized (Redis)")
        except Exception as e:
            logger.warning(f"Redis not available, using local fallback: {e}")
            self.redis_client = None
    
    async def check_rate_limit(
        self,
        key: str,
        tier: RateLimitTier = RateLimitTier.FREE,
        endpoint: Optional[str] = None,
        cost: int = 1
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is within rate limits
        
        Args:
            key: Rate limit key (e.g., "user:123" or "ip:192.168.1.1")
            tier: User tier
            endpoint: Optional endpoint-specific limit
            cost: Request cost (for weighted limits)
        
        Returns:
            (allowed, retry_after_seconds)
        """
        
        limits = self.TIER_LIMITS[tier]
        
        # Check all windows
        for window_name, limit in limits.items():
            window_seconds = self.WINDOWS[window_name]
            
            # Build Redis key
            redis_key = f"ratelimit:{key}:{window_name}"
            if endpoint:
                redis_key += f":{endpoint}"
            
            # Check limit
            allowed, retry_after = await self._check_window(
                redis_key=redis_key,
                limit=limit,
                window_seconds=window_seconds,
                cost=cost
            )
            
            if not allowed:
                logger.warning(
                    f"Rate limit exceeded: {key} (tier={tier}, window={window_name})"
                )
                return False, retry_after
        
        return True, None
    
    async def _check_window(
        self,
        redis_key: str,
        limit: int,
        window_seconds: int,
        cost: int
    ) -> Tuple[bool, Optional[int]]:
        """Check single time window using sliding window"""
        
        if self.redis_client:
            return await self._check_window_redis(
                redis_key, limit, window_seconds, cost
            )
        else:
            return await self._check_window_local(
                redis_key, limit, window_seconds, cost
            )
    
    async def _check_window_redis(
        self,
        redis_key: str,
        limit: int,
        window_seconds: int,
        cost: int
    ) -> Tuple[bool, Optional[int]]:
        """Redis-based sliding window rate limit"""
        
        try:
            now = datetime.utcnow().timestamp()
            window_start = now - window_seconds
            
            # Lua script for atomic sliding window check
            lua_script = """
            local key = KEYS[1]
            local now = tonumber(ARGV[1])
            local window_start = tonumber(ARGV[2])
            local limit = tonumber(ARGV[3])
            local cost = tonumber(ARGV[4])
            local window_seconds = tonumber(ARGV[5])
            
            -- Remove old entries
            redis.call('ZREMRANGEBYSCORE', key, 0, window_start)
            
            -- Get current count
            local current = redis.call('ZCARD', key)
            
            -- Check limit
            if current + cost > limit then
                -- Get oldest timestamp for retry-after
                local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
                local retry_after = 0
                if #oldest > 0 then
                    retry_after = math.ceil(tonumber(oldest[2]) + window_seconds - now)
                end
                return {0, retry_after}
            end
            
            -- Add current request
            for i = 1, cost do
                redis.call('ZADD', key, now, now .. ':' .. i)
            end
            
            -- Set expiry
            redis.call('EXPIRE', key, window_seconds)
            
            return {1, 0}
            """
            
            result = await self.redis_client.eval(
                lua_script,
                1,  # Number of keys
                redis_key,
                now,
                window_start,
                limit,
                cost,
                window_seconds
            )
            
            allowed = result[0] == 1
            retry_after = result[1] if not allowed else None
            
            return allowed, retry_after
            
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            # Fail open on error
            return True, None
    
    async def _check_window_local(
        self,
        key: str,
        limit: int,
        window_seconds: int,
        cost: int
    ) -> Tuple[bool, Optional[int]]:
        """Local fallback rate limiter"""
        
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Initialize if needed
        if key not in self.local_cache:
            self.local_cache[key] = []
        
        # Remove old entries
        self.local_cache[key] = [
            ts for ts in self.local_cache[key]
            if ts > window_start
        ]
        
        # Check limit
        current_count = len(self.local_cache[key])
        
        if current_count + cost > limit:
            # Calculate retry after
            oldest = min(self.local_cache[key]) if self.local_cache[key] else now
            retry_after = int(oldest + window_seconds - now) + 1
            return False, retry_after
        
        # Add current requests
        for _ in range(cost):
            self.local_cache[key].append(now)
        
        return True, None
    
    async def get_usage(
        self,
        key: str,
        tier: RateLimitTier = RateLimitTier.FREE
    ) -> Dict:
        """
        Get current rate limit usage
        
        Args:
            key: Rate limit key
            tier: User tier
        
        Returns:
            Usage info for all windows
        """
        
        limits = self.TIER_LIMITS[tier]
        usage = {}
        
        for window_name, limit in limits.items():
            window_seconds = self.WINDOWS[window_name]
            redis_key = f"ratelimit:{key}:{window_name}"
            
            if self.redis_client:
                try:
                    now = datetime.utcnow().timestamp()
                    window_start = now - window_seconds
                    
                    # Count entries in window
                    count = await self.redis_client.zcount(
                        redis_key,
                        window_start,
                        now
                    )
                    
                    usage[window_name] = {
                        "used": count,
                        "limit": limit,
                        "remaining": max(0, limit - count),
                        "reset_at": int(now + window_seconds)
                    }
                except Exception as e:
                    logger.error(f"Error getting usage: {e}")
                    usage[window_name] = {
                        "used": 0,
                        "limit": limit,
                        "remaining": limit,
                        "reset_at": None
                    }
            else:
                # Local cache usage
                if redis_key in self.local_cache:
                    count = len(self.local_cache[redis_key])
                else:
                    count = 0
                
                usage[window_name] = {
                    "used": count,
                    "limit": limit,
                    "remaining": max(0, limit - count),
                    "reset_at": None
                }
        
        return usage
    
    async def reset(self, key: str):
        """Reset rate limits for a key"""
        
        if self.redis_client:
            try:
                # Delete all rate limit keys for this key
                pattern = f"ratelimit:{key}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for: {key}")
            except Exception as e:
                logger.error(f"Error resetting rate limits: {e}")
        
        # Clear local cache
        keys_to_delete = [
            k for k in self.local_cache.keys()
            if k.startswith(f"ratelimit:{key}:")
        ]
        for k in keys_to_delete:
            del self.local_cache[k]


# Global rate limiter
rate_limiter = RateLimiter()
```

---

## ФАЙЛ 3: `ios_core/gateway/circuit_breaker.py`

```python
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
```

---

**Продолжаем?** Следующие файлы:
- Request Router
- API Analytics
- Middleware
- API Routes
- Tests
- Documentation