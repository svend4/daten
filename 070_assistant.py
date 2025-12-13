Продолжаем Week 21-22. Сейчас создадим:
- Тесты для gateway компонентов
- Docker конфигурацию
- Документацию
- Переходим к Day 129-130: Webhook System & Event Bus

Давайте создадим тесты и затем начнем webhook систему.# 🚪 DAY 127-128: API GATEWAY & RATE LIMITING (ЗАВЕРШЕНИЕ)

---

## ФАЙЛ 8: `tests/gateway/test_rate_limiter.py`

```python
"""
Tests for rate limiter
"""

import pytest
import asyncio
from ios_core.gateway.rate_limiter import rate_limiter, RateLimitTier


@pytest.fixture
async def limiter():
    """Initialize rate limiter"""
    await rate_limiter.initialize()
    yield rate_limiter
    # Cleanup
    await rate_limiter.reset("test:user")


@pytest.mark.asyncio
async def test_rate_limit_basic(limiter):
    """Test basic rate limiting"""
    
    key = "test:user"
    
    # First request should pass
    allowed, retry_after = await limiter.check_rate_limit(
        key=key,
        tier=RateLimitTier.FREE
    )
    
    assert allowed is True
    assert retry_after is None


@pytest.mark.asyncio
async def test_rate_limit_exceeded(limiter):
    """Test rate limit exceeded"""
    
    key = "test:user_heavy"
    tier = RateLimitTier.FREE
    
    # Get limit for second window
    limit = limiter.TIER_LIMITS[tier]["second"]
    
    # Make requests up to limit
    for i in range(limit):
        allowed, _ = await limiter.check_rate_limit(key=key, tier=tier)
        assert allowed is True, f"Request {i+1}/{limit} should be allowed"
    
    # Next request should fail
    allowed, retry_after = await limiter.check_rate_limit(key=key, tier=tier)
    
    assert allowed is False
    assert retry_after is not None
    assert retry_after > 0


@pytest.mark.asyncio
async def test_tier_differences(limiter):
    """Test different tier limits"""
    
    free_limit = limiter.TIER_LIMITS[RateLimitTier.FREE]["minute"]
    premium_limit = limiter.TIER_LIMITS[RateLimitTier.PREMIUM]["minute"]
    
    assert premium_limit > free_limit


@pytest.mark.asyncio
async def test_get_usage(limiter):
    """Test getting usage statistics"""
    
    key = "test:user_usage"
    tier = RateLimitTier.FREE
    
    # Make some requests
    for _ in range(3):
        await limiter.check_rate_limit(key=key, tier=tier)
    
    # Get usage
    usage = await limiter.get_usage(key=key, tier=tier)
    
    assert "second" in usage
    assert "minute" in usage
    assert usage["second"]["used"] >= 3
    assert usage["second"]["limit"] > 0


@pytest.mark.asyncio
async def test_reset(limiter):
    """Test resetting rate limits"""
    
    key = "test:user_reset"
    tier = RateLimitTier.FREE
    
    # Use up some quota
    for _ in range(5):
        await limiter.check_rate_limit(key=key, tier=tier)
    
    # Reset
    await limiter.reset(key)
    
    # Usage should be cleared
    usage = await limiter.get_usage(key=key, tier=tier)
    assert usage["second"]["used"] == 0
```

---

## ФАЙЛ 9: `tests/gateway/test_circuit_breaker.py`

```python
"""
Tests for circuit breaker
"""

import pytest
from ios_core.gateway.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitBreakerOpenError
)


@pytest.fixture
def breaker():
    """Create circuit breaker"""
    return CircuitBreaker(
        name="test",
        failure_threshold=3,
        recovery_timeout=1,
        half_open_max_calls=2
    )


@pytest.mark.asyncio
async def test_circuit_closed_initially(breaker):
    """Test circuit starts in CLOSED state"""
    
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_successful_call(breaker):
    """Test successful call through circuit"""
    
    async def success_func():
        return "success"
    
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


@pytest.mark.asyncio
async def test_failed_call(breaker):
    """Test failed call increases failure count"""
    
    async def fail_func():
        raise Exception("Test error")
    
    with pytest.raises(Exception):
        await breaker.call(fail_func)
    
    assert breaker.failure_count == 1
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_opens(breaker):
    """Test circuit opens after threshold"""
    
    async def fail_func():
        raise Exception("Test error")
    
    # Fail threshold times
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # Circuit should be open
    assert breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_blocks_when_open(breaker):
    """Test circuit blocks calls when open"""
    
    async def fail_func():
        raise Exception("Test error")
    
    # Open circuit
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    # Next call should be blocked
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(fail_func)


@pytest.mark.asyncio
async def test_circuit_recovery(breaker):
    """Test circuit recovery after timeout"""
    
    import asyncio
    
    async def fail_func():
        raise Exception("Test error")
    
    async def success_func():
        return "success"
    
    # Open circuit
    for _ in range(breaker.failure_threshold):
        with pytest.raises(Exception):
            await breaker.call(fail_func)
    
    assert breaker.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    await asyncio.sleep(breaker.recovery_timeout + 0.1)
    
    # Next call should transition to HALF_OPEN
    result = await breaker.call(success_func)
    
    assert result == "success"
    assert breaker.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_get_state(breaker):
    """Test getting circuit state"""
    
    state = breaker.get_state()
    
    assert "name" in state
    assert "state" in state
    assert state["name"] == "test"
    assert state["state"] == CircuitState.CLOSED.value
```

---

## ФАЙЛ 10: `docs/API_GATEWAY_GUIDE.md`

```markdown
# API Gateway Guide

## Overview

The IOS System API Gateway provides enterprise-grade request management:

- **Multi-tier Rate Limiting** - Protect against abuse
- **Circuit Breaker** - Fault tolerance for external services
- **Load Balancing** - Distribute traffic across backends
- **Analytics** - Track API usage and performance

---

## Rate Limiting

### Features

- Multiple time windows (second, minute, hour, day)
- User-tier based limits
- Sliding window algorithm
- Automatic retry-after headers
- Redis-backed with local fallback

### Tiers

| Tier | Second | Minute | Hour | Day |
|------|--------|--------|------|-----|
| Free | 2 | 60 | 1,000 | 10,000 |
| Basic | 5 | 150 | 5,000 | 50,000 |
| Premium | 10 | 300 | 15,000 | 200,000 |
| Enterprise | 50 | 1,000 | 50,000 | 1,000,000 |

### Usage

**Check Rate Limit:**

```python
from ios_core.gateway.rate_limiter import rate_limiter, RateLimitTier

allowed, retry_after = await rate_limiter.check_rate_limit(
    key="user:123",
    tier=RateLimitTier.PREMIUM
)

if not allowed:
    raise HTTPException(429, f"Retry after {retry_after}s")
```

**Get Usage:**

```python
usage = await rate_limiter.get_usage("user:123", RateLimitTier.PREMIUM)

print(usage["minute"])
# {
#   "used": 45,
#   "limit": 300,
#   "remaining": 255,
#   "reset_at": 1640000000
# }
```

**API Endpoint:**

```bash
GET /api/rate-limit/usage
Authorization: Bearer <token>

Response:
{
  "key": "user:123",
  "tier": "premium",
  "usage": {
    "second": {"used": 2, "limit": 10, "remaining": 8},
    "minute": {"used": 45, "limit": 300, "remaining": 255},
    "hour": {"used": 1200, "limit": 15000, "remaining": 13800},
    "day": {"used": 25000, "limit": 200000, "remaining": 175000}
  }
}
```

### Response Headers

Every API response includes rate limit headers:

```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 255
X-RateLimit-Reset: 1640000000
```

---

## Circuit Breaker

### Overview

Protects against cascading failures when calling external services.

**States:**
- **CLOSED**: Normal operation, all requests pass through
- **OPEN**: Too many failures, requests blocked
- **HALF_OPEN**: Testing if service recovered

### Configuration

```python
from ios_core.gateway.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(
    name="external_api",
    failure_threshold=5,      # Open after 5 failures
    recovery_timeout=60,      # Wait 60s before testing
    half_open_max_calls=3     # 3 successful calls to close
)
```

### Usage

**Decorator:**

```python
@breaker.protected
async def call_external_api(data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/process",
            json=data
        )
        return response.json()
```

**Manual:**

```python
try:
    result = await breaker.call(risky_operation, arg1, arg2)
except CircuitBreakerOpenError:
    # Circuit is open, use fallback
    result = get_cached_data()
```

**Check State:**

```bash
GET /api/circuit-breaker/status
Authorization: Bearer <token>

Response:
{
  "circuit_breakers": {
    "external_api": {
      "state": "closed",
      "failure_count": 2,
      "total_calls": 1500,
      "failure_rate": 3.2
    }
  }
}
```

---

## Load Balancing

### Strategies

1. **Round Robin** - Distribute evenly
2. **Weighted** - Based on server capacity
3. **Least Connections** - Route to least busy
4. **Sticky Session** - Keep user on same server

### Setup

```python
from ios_core.gateway.request_router import request_router, RoutingStrategy

# Add backends
request_router.add_backend(
    name="server1",
    url="http://backend1:8000",
    weight=2
)

request_router.add_backend(
    name="server2", 
    url="http://backend2:8000",
    weight=1
)

# Route request
backend = request_router.route(
    strategy=RoutingStrategy.WEIGHTED,
    session_id="user123"
)

# Make request to selected backend
async with httpx.AsyncClient() as client:
    response = await client.get(f"{backend.url}/api/data")
```

### Health Checks

Automatic health monitoring:

```bash
POST /api/router/health-check
Authorization: Bearer <token>

Response:
{
  "backends": {
    "server1": {
      "is_healthy": true,
      "active_connections": 12,
      "avg_response_time": 0.15,
      "error_rate": 0.5
    }
  }
}
```

---

## Analytics

### Metrics Tracked

- Total requests
- Response times (avg, p95, p99)
- Status code distribution
- Error rates
- Endpoint popularity
- User activity

### Endpoints

**Summary:**

```bash
GET /api/analytics/summary

Response:
{
  "total_requests": 150000,
  "unique_endpoints": 45,
  "unique_users": 1250,
  "avg_response_time": 0.123,
  "total_errors": 250
}
```

**Endpoint Stats:**

```bash
GET /api/analytics/endpoints?endpoint=/api/search

Response:
{
  "endpoint": "/api/search",
  "total_requests": 25000,
  "avg_response_time": 0.215,
  "p95_response_time": 0.450,
  "p99_response_time": 0.850
}
```

**Top Endpoints:**

```bash
GET /api/analytics/endpoints?limit=10

Response:
{
  "endpoints": [
    {
      "endpoint": "/api/search",
      "requests": 25000,
      "avg_response_time": 0.215
    }
  ]
}
```

---

## Best Practices

### 1. Rate Limit Keys

```python
# User-based (authenticated)
key = f"user:{user_id}"

# IP-based (unauthenticated)
key = f"ip:{request.client.host}"

# Endpoint-specific
key = f"user:{user_id}:endpoint:{endpoint}"
```

### 2. Circuit Breaker Placement

Use circuit breakers for:
- External API calls
- Database queries (if problematic)
- Long-running operations
- Third-party services

### 3. Load Balancing

- Use **Weighted** for servers with different capacities
- Use **Sticky Sessions** for stateful applications
- Use **Least Connections** for variable request times

### 4. Monitoring

Set up alerts for:
- Rate limit exceeded (>10% of users)
- Circuit breaker opens
- Backend health failures
- High error rates (>5%)
- Slow response times (p95 > 1s)

---

## Production Deployment

### Docker Compose

```yaml
services:
  api-gateway:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
      - RATE_LIMIT_ENABLED=true
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
```

### Environment Variables

```bash
# Rate Limiting
REDIS_URL=redis://localhost:6379
RATE_LIMIT_ENABLED=true

# Circuit Breaker
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Analytics
ANALYTICS_RETENTION_DAYS=30
```

---

## Troubleshooting

### Rate Limit Issues

**Problem:** Users getting rate limited too quickly

**Solutions:**
1. Check tier assignment
2. Review rate limit windows
3. Check for retry storms
4. Increase limits for specific users

### Circuit Breaker Issues

**Problem:** Circuit stays open

**Solutions:**
1. Check backend health
2. Review failure threshold
3. Increase recovery timeout
4. Manual reset if needed

### Load Balancing Issues

**Problem:** Uneven distribution

**Solutions:**
1. Check backend weights
2. Review routing strategy
3. Monitor connection counts
4. Check health check frequency

---

## API Reference

See [API Documentation](/api/docs) for complete endpoint reference.
```

---

# 📡 DAY 129-130: WEBHOOK SYSTEM & EVENT BUS

---

## 📊 ЦЕЛЬ

Создание асинхронной системы событий:
- **Webhook Management** - управление веб-хуками
- **Event Bus** - внутренняя шина событий
- **Async Processing** - асинхронная обработка
- **Retry Logic** - повторные попытки
- **Event Store** - хранение событий
- **Subscription Management** - управление подписками

---

## ФАЙЛ 11: `ios_core/events/__init__.py`

```python
"""
Event System Module
"""

from .event_bus import EventBus, event_bus
from .webhook_manager import WebhookManager, webhook_manager
from .event_store import EventStore, event_store
from .models import Event, EventType, WebhookSubscription

__all__ = [
    'EventBus',
    'event_bus',
    'WebhookManager',
    'webhook_manager',
    'EventStore',
    'event_store',
    'Event',
    'EventType',
    'WebhookSubscription',
]
```

---

## ФАЙЛ 12: `ios_core/events/models.py`

```python
"""
Event System Models
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..database import Base


class EventType(str, Enum):
    """Event types"""
    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_VIEWED = "document.viewed"
    
    # Search events
    SEARCH_PERFORMED = "search.performed"
    SEARCH_RESULT_CLICKED = "search.result_clicked"
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Security events
    SECURITY_BREACH_DETECTED = "security.breach_detected"
    MFA_ENABLED = "security.mfa_enabled"
    PASSWORD_CHANGED = "security.password_changed"
    
    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_ERROR = "system.error"
    BACKUP_COMPLETED = "system.backup_completed"
    
    # AI/ML events
    EMBEDDING_CREATED = "ml.embedding_created"
    GPT_GENERATION_COMPLETED = "ml.gpt_generation_completed"
    
    # Integration events
    WEBHOOK_DELIVERED = "integration.webhook_delivered"
    WEBHOOK_FAILED = "integration.webhook_failed"


class Event(BaseModel):
    """
    Event model
    
    Represents a system event that can be:
    - Published to event bus
    - Stored in event store
    - Delivered via webhooks
    """
    
    id: Optional[str] = None
    type: EventType
    source: str  # Service/component that generated event
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None  # For tracing related events
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookSubscription(Base):
    """
    Webhook subscription
    
    Allows external systems to receive events via HTTP callbacks.
    """
    
    __tablename__ = "webhook_subscriptions"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100))  # For signature verification
    
    # Event filtering
    event_types = Column(JSON)  # List of EventType values
    
    # Configuration
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    
    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="webhook_subscriptions")
    deliveries = relationship("WebhookDelivery", back_populates="subscription")


class WebhookDelivery(Base):
    """
    Webhook delivery attempt
    
    Tracks individual webhook deliveries for debugging and monitoring.
    """
    
    __tablename__ = "webhook_deliveries"
    
    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), ForeignKey("webhook_subscriptions.id"))
    event_id = Column(String(50))
    event_type = Column(String(100))
    
    # Request
    request_url = Column(String(500))
    request_payload = Column(JSON)
    request_headers = Column(JSON)
    
    # Response
    response_status = Column(Integer)
    response_body = Column(Text)
    response_time_ms = Column(Integer)
    
    # Status
    success = Column(Boolean)
    error_message = Column(Text)
    attempt_number = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    
    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")
```

---

## ФАЙЛ 13: `ios_core/events/event_bus.py`

```python
"""
Event Bus - Internal event distribution
"""

import logging
from typing import Callable, Dict, List, Set, Optional, Any
import asyncio
from datetime import datetime
from collections import defaultdict

from .models import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-memory event bus for internal event distribution
    
    Features:
    - Pub/Sub pattern
    - Async handlers
    - Event filtering
    - Error handling
    - Handler priorities
    
    Usage:
        bus = EventBus()
        
        # Subscribe
        @bus.subscribe(EventType.DOCUMENT_CREATED)
        async def on_document_created(event: Event):
            print(f"Document created: {event.data['id']}")
        
        # Publish
        await bus.publish(Event(
            type=EventType.DOCUMENT_CREATED,
            source="api",
            data={"id": "doc123"}
        ))
    """
    
    def __init__(self):
        # Handlers: EventType -> List[(priority, handler)]
        self.handlers: Dict[EventType, List[tuple[int, Callable]]] = defaultdict(list)
        
        # Wildcard handlers (receive all events)
        self.wildcard_handlers: List[tuple[int, Callable]] = []
        
        # Statistics
        self.published_count = 0
        self.delivered_count = 0
        self.error_count = 0
        
        # Queue for async processing
        self.event_queue = asyncio.Queue()
        self.is_running = False
    
    def subscribe(
        self,
        event_type: Optional[EventType] = None,
        priority: int = 0
    ):
        """
        Decorator to subscribe to events
        
        Args:
            event_type: Event type to listen for (None for all events)
            priority: Handler priority (higher = earlier execution)
        """
        
        def decorator(handler: Callable):
            if event_type is None:
                # Wildcard subscription
                self.wildcard_handlers.append((priority, handler))
                self.wildcard_handlers.sort(key=lambda x: x[0], reverse=True)
            else:
                # Specific event type
                self.handlers[event_type].append((priority, handler))
                self.handlers[event_type].sort(key=lambda x: x[0], reverse=True)
            
            logger.info(
                f"Subscribed {handler.__name__} to "
                f"{event_type.value if event_type else '*'} "
                f"(priority={priority})"
            )
            
            return handler
        
        return decorator
    
    async def publish(
        self,
        event: Event,
        wait: bool = False
    ):
        """
        Publish event to bus
        
        Args:
            event: Event to publish
            wait: If True, wait for handlers to complete
        """
        
        self.published_count += 1
        
        if not event.id:
            event.id = f"evt_{datetime.utcnow().timestamp()}"
        
        logger.debug(f"Publishing event: {event.type.value} (id={event.id})")
        
        if wait:
            # Synchronous delivery
            await self._deliver_event(event)
        else:
            # Async delivery via queue
            await self.event_queue.put(event)
    
    async def _deliver_event(self, event: Event):
        """Deliver event to all subscribed handlers"""
        
        # Get handlers for this event type
        type_handlers = self.handlers.get(event.type, [])
        
        # Combine with wildcard handlers
        all_handlers = type_handlers + self.wildcard_handlers
        
        # Sort by priority
        all_handlers.sort(key=lambda x: x[0], reverse=True)
        
        # Execute handlers
        for priority, handler in all_handlers:
            try:
                await handler(event)
                self.delivered_count += 1
                
                logger.debug(
                    f"Delivered {event.type.value} to {handler.__name__}"
                )
                
            except Exception as e:
                self.error_count += 1
                logger.error(
                    f"Error in handler {handler.__name__} "
                    f"for event {event.type.value}: {e}",
                    exc_info=True
                )
    
    async def start(self):
        """Start event processing loop"""
        
        if self.is_running:
            logger.warning("Event bus already running")
            return
        
        self.is_running = True
        logger.info("Event bus started")
        
        # Process events from queue
        while self.is_running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                await self._deliver_event(event)
                
            except asyncio.TimeoutError:
                # No events, continue
                continue
            
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
    
    def stop(self):
        """Stop event processing loop"""
        
        self.is_running = False
        logger.info("Event bus stopped")
    
    def get_stats(self) -> Dict:
        """Get event bus statistics"""
        
        total_handlers = sum(len(h) for h in self.handlers.values())
        total_handlers += len(self.wildcard_handlers)
        
        return {
            "published": self.published_count,
            "delivered": self.delivered_count,
            "errors": self.error_count,
            "total_handlers": total_handlers,
            "event_types": len(self.handlers),
            "queue_size": self.event_queue.qsize(),
            "is_running": self.is_running
        }


# Global event bus
event_bus = EventBus()
```

---

**Продолжение следует...**

Создано:
- ✅ Event Models (Event, EventType, WebhookSubscription)
- ✅ Event Bus (pub/sub pattern)
- ✅ Tests for Gateway components
- ✅ API Gateway Documentation

**Следующие файлы:**
- Webhook Manager
- Event Store
- Webhook Routes
- Integration examples
- Full documentation

**Готовы продолжить?**