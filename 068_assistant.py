Продолжаю Week 21-22, Day 127-128: API Gateway & Rate Limiting. Следующие файлы:
- Request Router
- API Analytics
- Middleware
- API Routes
- Tests
- Documentation# 🚪 DAY 127-128: API GATEWAY & RATE LIMITING (ПРОДОЛЖЕНИЕ)

---

## ФАЙЛ 4: `ios_core/gateway/request_router.py`

```python
"""
Intelligent Request Router
Dynamic routing with load balancing
"""

import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
import random
from enum import Enum

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Routing strategies"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"
    STICKY_SESSION = "sticky_session"


class Backend:
    """Backend server"""
    
    def __init__(
        self,
        name: str,
        url: str,
        weight: int = 1,
        health_check_url: Optional[str] = None
    ):
        self.name = name
        self.url = url
        self.weight = weight
        self.health_check_url = health_check_url or f"{url}/health"
        
        # State
        self.is_healthy = True
        self.active_connections = 0
        self.total_requests = 0
        self.total_errors = 0
        self.last_health_check = None
        self.response_times = []
    
    def record_request(self, success: bool, response_time: float):
        """Record request metrics"""
        
        self.total_requests += 1
        if not success:
            self.total_errors += 1
        
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
    
    def get_avg_response_time(self) -> float:
        """Get average response time"""
        
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_error_rate(self) -> float:
        """Get error rate percentage"""
        
        if self.total_requests == 0:
            return 0.0
        return (self.total_errors / self.total_requests) * 100


class RequestRouter:
    """
    Intelligent request router with load balancing
    
    Features:
    - Multiple routing strategies
    - Health checks
    - Automatic failover
    - Connection tracking
    - Weighted distribution
    - Sticky sessions
    
    Usage:
        router = RequestRouter()
        
        # Add backends
        router.add_backend("server1", "http://localhost:8001", weight=2)
        router.add_backend("server2", "http://localhost:8002", weight=1)
        
        # Route request
        backend = router.route(
            session_id="user123",
            strategy=RoutingStrategy.WEIGHTED
        )
    """
    
    def __init__(self):
        self.backends: Dict[str, Backend] = {}
        self.round_robin_index = 0
        self.sticky_sessions: Dict[str, str] = {}  # session_id -> backend_name
    
    def add_backend(
        self,
        name: str,
        url: str,
        weight: int = 1,
        health_check_url: Optional[str] = None
    ):
        """Add backend server"""
        
        backend = Backend(
            name=name,
            url=url,
            weight=weight,
            health_check_url=health_check_url
        )
        
        self.backends[name] = backend
        logger.info(f"Added backend: {name} ({url}) weight={weight}")
    
    def remove_backend(self, name: str):
        """Remove backend server"""
        
        if name in self.backends:
            del self.backends[name]
            logger.info(f"Removed backend: {name}")
    
    def route(
        self,
        strategy: RoutingStrategy = RoutingStrategy.ROUND_ROBIN,
        session_id: Optional[str] = None,
        exclude: Optional[List[str]] = None
    ) -> Optional[Backend]:
        """
        Route request to backend
        
        Args:
            strategy: Routing strategy
            session_id: Session ID for sticky sessions
            exclude: Backends to exclude
        
        Returns:
            Selected backend or None if all unhealthy
        """
        
        # Get healthy backends
        healthy_backends = [
            b for b in self.backends.values()
            if b.is_healthy and (not exclude or b.name not in exclude)
        ]
        
        if not healthy_backends:
            logger.error("No healthy backends available")
            return None
        
        # Route based on strategy
        if strategy == RoutingStrategy.STICKY_SESSION and session_id:
            return self._route_sticky_session(session_id, healthy_backends)
        
        elif strategy == RoutingStrategy.ROUND_ROBIN:
            return self._route_round_robin(healthy_backends)
        
        elif strategy == RoutingStrategy.WEIGHTED:
            return self._route_weighted(healthy_backends)
        
        elif strategy == RoutingStrategy.LEAST_CONNECTIONS:
            return self._route_least_connections(healthy_backends)
        
        elif strategy == RoutingStrategy.RANDOM:
            return random.choice(healthy_backends)
        
        else:
            logger.warning(f"Unknown strategy: {strategy}, using random")
            return random.choice(healthy_backends)
    
    def _route_sticky_session(
        self,
        session_id: str,
        healthy_backends: List[Backend]
    ) -> Backend:
        """Route with sticky sessions"""
        
        # Check if session already mapped
        if session_id in self.sticky_sessions:
            backend_name = self.sticky_sessions[session_id]
            
            # Check if backend still healthy
            if backend_name in self.backends:
                backend = self.backends[backend_name]
                if backend.is_healthy:
                    return backend
        
        # No existing mapping or backend unhealthy, assign new
        backend = self._route_weighted(healthy_backends)
        self.sticky_sessions[session_id] = backend.name
        
        return backend
    
    def _route_round_robin(self, healthy_backends: List[Backend]) -> Backend:
        """Round-robin routing"""
        
        backend = healthy_backends[self.round_robin_index % len(healthy_backends)]
        self.round_robin_index += 1
        
        return backend
    
    def _route_weighted(self, healthy_backends: List[Backend]) -> Backend:
        """Weighted random routing"""
        
        total_weight = sum(b.weight for b in healthy_backends)
        
        if total_weight == 0:
            return random.choice(healthy_backends)
        
        # Random selection based on weights
        rand = random.uniform(0, total_weight)
        current = 0
        
        for backend in healthy_backends:
            current += backend.weight
            if rand <= current:
                return backend
        
        return healthy_backends[-1]
    
    def _route_least_connections(self, healthy_backends: List[Backend]) -> Backend:
        """Route to backend with least active connections"""
        
        return min(healthy_backends, key=lambda b: b.active_connections)
    
    async def health_check(self, backend_name: str) -> bool:
        """
        Perform health check on backend
        
        Args:
            backend_name: Backend name
        
        Returns:
            True if healthy
        """
        
        if backend_name not in self.backends:
            return False
        
        backend = self.backends[backend_name]
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    backend.health_check_url,
                    timeout=5.0
                )
                
                is_healthy = response.status_code == 200
                backend.is_healthy = is_healthy
                backend.last_health_check = datetime.utcnow()
                
                if is_healthy:
                    logger.debug(f"Backend {backend_name} is healthy")
                else:
                    logger.warning(
                        f"Backend {backend_name} unhealthy: "
                        f"status={response.status_code}"
                    )
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Health check failed for {backend_name}: {e}")
            backend.is_healthy = False
            backend.last_health_check = datetime.utcnow()
            return False
    
    async def health_check_all(self):
        """Run health checks on all backends"""
        
        import asyncio
        
        tasks = [
            self.health_check(name)
            for name in self.backends.keys()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        healthy_count = sum(1 for r in results if r is True)
        
        logger.info(
            f"Health check complete: {healthy_count}/{len(self.backends)} healthy"
        )
    
    def get_backend_stats(self) -> Dict:
        """Get statistics for all backends"""
        
        return {
            name: {
                "url": backend.url,
                "weight": backend.weight,
                "is_healthy": backend.is_healthy,
                "active_connections": backend.active_connections,
                "total_requests": backend.total_requests,
                "total_errors": backend.total_errors,
                "error_rate": round(backend.get_error_rate(), 2),
                "avg_response_time": round(backend.get_avg_response_time(), 2),
                "last_health_check": backend.last_health_check.isoformat()
                    if backend.last_health_check else None
            }
            for name, backend in self.backends.items()
        }


# Global request router
request_router = RequestRouter()
```

---

## ФАЙЛ 5: `ios_core/gateway/api_analytics.py`

```python
"""
API Analytics and Monitoring
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import asyncio

from ..database import async_session
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


class APIAnalytics:
    """
    API usage analytics
    
    Features:
    - Request tracking
    - Response time metrics
    - Error rate monitoring
    - Endpoint popularity
    - User behavior analysis
    - Rate limit monitoring
    
    Usage:
        analytics = APIAnalytics()
        
        # Track request
        await analytics.track_request(
            endpoint="/api/search",
            method="POST",
            user_id="user123",
            response_time=0.15,
            status_code=200
        )
    """
    
    def __init__(self):
        self.memory_stats = {
            "requests_by_endpoint": defaultdict(int),
            "requests_by_user": defaultdict(int),
            "response_times": defaultdict(list),
            "status_codes": defaultdict(int),
            "errors": [],
        }
        self.retention_days = 30
    
    async def track_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        response_time: float = 0.0,
        status_code: int = 200,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Track API request
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            user_id: User ID
            response_time: Response time in seconds
            status_code: HTTP status code
            error: Error message if any
            metadata: Additional metadata
        """
        
        # Update memory stats
        self.memory_stats["requests_by_endpoint"][endpoint] += 1
        
        if user_id:
            self.memory_stats["requests_by_user"][user_id] += 1
        
        self.memory_stats["response_times"][endpoint].append(response_time)
        self.memory_stats["status_codes"][status_code] += 1
        
        if error:
            self.memory_stats["errors"].append({
                "endpoint": endpoint,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Keep only recent errors
            if len(self.memory_stats["errors"]) > 1000:
                self.memory_stats["errors"] = self.memory_stats["errors"][-1000:]
        
        # Trim response times lists
        for ep in self.memory_stats["response_times"]:
            times = self.memory_stats["response_times"][ep]
            if len(times) > 1000:
                self.memory_stats["response_times"][ep] = times[-1000:]
    
    def get_endpoint_stats(
        self,
        endpoint: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """
        Get endpoint statistics
        
        Args:
            endpoint: Specific endpoint (None for all)
            limit: Max endpoints to return
        
        Returns:
            Endpoint statistics
        """
        
        if endpoint:
            # Specific endpoint
            times = self.memory_stats["response_times"].get(endpoint, [])
            count = self.memory_stats["requests_by_endpoint"].get(endpoint, 0)
            
            return {
                "endpoint": endpoint,
                "total_requests": count,
                "avg_response_time": round(sum(times) / len(times), 3) if times else 0,
                "min_response_time": round(min(times), 3) if times else 0,
                "max_response_time": round(max(times), 3) if times else 0,
                "p95_response_time": round(
                    self._percentile(times, 95), 3
                ) if times else 0,
                "p99_response_time": round(
                    self._percentile(times, 99), 3
                ) if times else 0
            }
        
        else:
            # Top endpoints
            top_endpoints = sorted(
                self.memory_stats["requests_by_endpoint"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "endpoints": [
                    {
                        "endpoint": ep,
                        "requests": count,
                        "avg_response_time": round(
                            sum(self.memory_stats["response_times"].get(ep, [])) /
                            len(self.memory_stats["response_times"].get(ep, [1])),
                            3
                        )
                    }
                    for ep, count in top_endpoints
                ]
            }
    
    def get_user_stats(
        self,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict:
        """Get user statistics"""
        
        if user_id:
            # Specific user
            return {
                "user_id": user_id,
                "total_requests": self.memory_stats["requests_by_user"].get(
                    user_id, 0
                )
            }
        
        else:
            # Top users
            top_users = sorted(
                self.memory_stats["requests_by_user"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:limit]
            
            return {
                "users": [
                    {"user_id": uid, "requests": count}
                    for uid, count in top_users
                ]
            }
    
    def get_error_stats(self, limit: int = 100) -> Dict:
        """Get error statistics"""
        
        recent_errors = self.memory_stats["errors"][-limit:]
        
        # Group by endpoint
        errors_by_endpoint = defaultdict(int)
        for error in recent_errors:
            errors_by_endpoint[error["endpoint"]] += 1
        
        return {
            "total_errors": len(self.memory_stats["errors"]),
            "recent_errors": recent_errors,
            "by_endpoint": dict(errors_by_endpoint)
        }
    
    def get_status_code_stats(self) -> Dict:
        """Get HTTP status code distribution"""
        
        total = sum(self.memory_stats["status_codes"].values())
        
        return {
            "distribution": dict(self.memory_stats["status_codes"]),
            "total_requests": total,
            "success_rate": round(
                sum(
                    count for code, count in self.memory_stats["status_codes"].items()
                    if 200 <= code < 300
                ) / total * 100, 2
            ) if total > 0 else 0
        }
    
    def get_summary(self) -> Dict:
        """Get overall summary"""
        
        total_requests = sum(self.memory_stats["requests_by_endpoint"].values())
        
        # Calculate overall avg response time
        all_times = []
        for times in self.memory_stats["response_times"].values():
            all_times.extend(times)
        
        avg_response_time = sum(all_times) / len(all_times) if all_times else 0
        
        return {
            "total_requests": total_requests,
            "unique_endpoints": len(self.memory_stats["requests_by_endpoint"]),
            "unique_users": len(self.memory_stats["requests_by_user"]),
            "avg_response_time": round(avg_response_time, 3),
            "total_errors": len(self.memory_stats["errors"]),
            "status_codes": dict(self.memory_stats["status_codes"])
        }
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def reset(self):
        """Reset all statistics"""
        
        self.memory_stats = {
            "requests_by_endpoint": defaultdict(int),
            "requests_by_user": defaultdict(int),
            "response_times": defaultdict(list),
            "status_codes": defaultdict(int),
            "errors": [],
        }
        
        logger.info("API analytics reset")


# Global API analytics
api_analytics = APIAnalytics()
```

---

## ФАЙЛ 6: `api/middleware/gateway_middleware.py`

```python
"""
API Gateway Middleware
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from ios_core.gateway.rate_limiter import rate_limiter, RateLimitTier
from ios_core.gateway.api_analytics import api_analytics
from ios_core.security.rbac import rbac_manager

logger = logging.getLogger(__name__)


class GatewayMiddleware(BaseHTTPMiddleware):
    """
    API Gateway middleware
    
    Features:
    - Rate limiting
    - Analytics tracking
    - Response time measurement
    - Error tracking
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through gateway"""
        
        start_time = time.time()
        error = None
        
        try:
            # Extract user info
            user_id = None
            tier = RateLimitTier.FREE
            
            # Try to get user from auth
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = user.get("user_id")
                
                # Get user tier (from database or token)
                # For now, use default tier
                tier = RateLimitTier.PREMIUM if user.get("is_premium") else RateLimitTier.BASIC
            
            # Build rate limit key
            if user_id:
                rate_limit_key = f"user:{user_id}"
            else:
                # Use IP for unauthenticated requests
                client_ip = request.client.host
                rate_limit_key = f"ip:{client_ip}"
                tier = RateLimitTier.FREE
            
            # Check rate limit
            allowed, retry_after = await rate_limiter.check_rate_limit(
                key=rate_limit_key,
                tier=tier,
                endpoint=request.url.path
            )
            
            if not allowed:
                # Add rate limit headers
                response = Response(
                    content='{"error": "Rate limit exceeded"}',
                    status_code=429,
                    media_type="application/json"
                )
                response.headers["Retry-After"] = str(retry_after)
                response.headers["X-RateLimit-Limit"] = "See /api/rate-limit/usage"
                
                # Track request
                await api_analytics.track_request(
                    endpoint=request.url.path,
                    method=request.method,
                    user_id=user_id,
                    status_code=429,
                    error="Rate limit exceeded"
                )
                
                return response
            
            # Get rate limit usage for headers
            usage = await rate_limiter.get_usage(rate_limit_key, tier)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            if "minute" in usage:
                response.headers["X-RateLimit-Limit"] = str(usage["minute"]["limit"])
                response.headers["X-RateLimit-Remaining"] = str(usage["minute"]["remaining"])
                if usage["minute"]["reset_at"]:
                    response.headers["X-RateLimit-Reset"] = str(usage["minute"]["reset_at"])
            
            return response
            
        except Exception as e:
            logger.error(f"Gateway middleware error: {e}", exc_info=True)
            error = str(e)
            raise
            
        finally:
            # Calculate response time
            response_time = time.time() - start_time
            
            # Track analytics
            try:
                await api_analytics.track_request(
                    endpoint=request.url.path,
                    method=request.method,
                    user_id=user_id if user_id else None,
                    response_time=response_time,
                    status_code=response.status_code if 'response' in locals() else 500,
                    error=error
                )
            except Exception as e:
                logger.error(f"Failed to track analytics: {e}")
```

---

## ФАЙЛ 7: `api/routes/gateway_api.py`

```python
"""
API Gateway Management Routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ios_core.gateway.rate_limiter import rate_limiter, RateLimitTier
from ios_core.gateway.circuit_breaker import circuit_breaker
from ios_core.gateway.request_router import request_router, RoutingStrategy
from ios_core.gateway.api_analytics import api_analytics
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


# === Rate Limiting ===

class RateLimitUsageRequest(BaseModel):
    key: str
    tier: RateLimitTier = RateLimitTier.FREE


@router.get("/rate-limit/usage")
async def get_rate_limit_usage(
    tier: RateLimitTier = RateLimitTier.FREE,
    current_user: dict = Depends(get_current_user)
):
    """
    Get current rate limit usage
    
    Returns usage for all time windows (second, minute, hour, day).
    """
    
    user_id = current_user["user_id"]
    key = f"user:{user_id}"
    
    usage = await rate_limiter.get_usage(key, tier)
    
    return {
        "key": key,
        "tier": tier.value,
        "usage": usage
    }


@router.post("/rate-limit/reset")
@require_permission(Permission.SYSTEM_ADMIN)
async def reset_rate_limit(
    key: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Reset rate limits for a key
    
    Requires: SYSTEM_ADMIN permission
    """
    
    await rate_limiter.reset(key)
    
    return {
        "message": f"Rate limits reset for: {key}"
    }


# === Circuit Breaker ===

@router.get("/circuit-breaker/status")
@require_permission(Permission.SYSTEM_READ)
async def get_circuit_breaker_status(
    current_user: dict = Depends(get_current_user)
):
    """
    Get status of all circuit breakers
    
    Requires: SYSTEM_READ permission
    """
    
    states = circuit_breaker.get_all_states()
    
    return {
        "circuit_breakers": states,
        "total": len(states),
        "open": sum(1 for s in states.values() if s["state"] == "open"),
        "half_open": sum(1 for s in states.values() if s["state"] == "half_open"),
        "closed": sum(1 for s in states.values() if s["state"] == "closed")
    }


@router.post("/circuit-breaker/{name}/reset")
@require_permission(Permission.SYSTEM_ADMIN)
async def reset_circuit_breaker(
    name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Manually reset a circuit breaker
    
    Requires: SYSTEM_ADMIN permission
    """
    
    breaker = circuit_breaker.get_or_create(name)
    await breaker.reset()
    
    return {
        "message": f"Circuit breaker '{name}' reset",
        "state": breaker.get_state()
    }


# === Request Router ===

class AddBackendRequest(BaseModel):
    name: str
    url: str
    weight: int = 1
    health_check_url: Optional[str] = None


@router.post("/router/backends")
@require_permission(Permission.SYSTEM_ADMIN)
async def add_backend(
    request: AddBackendRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Add backend server
    
    Requires: SYSTEM_ADMIN permission
    """
    
    request_router.add_backend(
        name=request.name,
        url=request.url,
        weight=request.weight,
        health_check_url=request.health_check_url
    )
    
    return {
        "message": f"Backend '{request.name}' added",
        "backend": {
            "name": request.name,
            "url": request.url,
            "weight": request.weight
        }
    }


@router.delete("/router/backends/{name}")
@require_permission(Permission.SYSTEM_ADMIN)
async def remove_backend(
    name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove backend server
    
    Requires: SYSTEM_ADMIN permission
    """
    
    request_router.remove_backend(name)
    
    return {
        "message": f"Backend '{name}' removed"
    }


@router.get("/router/backends")
@require_permission(Permission.SYSTEM_READ)
async def get_backends(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all backend servers with statistics
    
    Requires: SYSTEM_READ permission
    """
    
    stats = request_router.get_backend_stats()
    
    return {
        "backends": stats,
        "total": len(stats),
        "healthy": sum(1 for b in stats.values() if b["is_healthy"])
    }


@router.post("/router/health-check")
@require_permission(Permission.SYSTEM_ADMIN)
async def run_health_checks(
    current_user: dict = Depends(get_current_user)
):
    """
    Run health checks on all backends
    
    Requires: SYSTEM_ADMIN permission
    """
    
    await request_router.health_check_all()
    
    stats = request_router.get_backend_stats()
    
    return {
        "message": "Health checks complete",
        "backends": stats
    }


# === Analytics ===

@router.get("/analytics/summary")
@require_permission(Permission.SYSTEM_READ)
async def get_analytics_summary(
    current_user: dict = Depends(get_current_user)
):
    """
    Get API analytics summary
    
    Requires: SYSTEM_READ permission
    """
    
    summary = api_analytics.get_summary()
    
    return summary


@router.get("/analytics/endpoints")
@require_permission(Permission.SYSTEM_READ)
async def get_endpoint_analytics(
    endpoint: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get endpoint statistics
    
    Requires: SYSTEM_READ permission
    """
    
    stats = api_analytics.get_endpoint_stats(endpoint, limit)
    
    return stats


@router.get("/analytics/users")
@require_permission(Permission.SYSTEM_READ)
async def get_user_analytics(
    user_id: Optional[str] = None,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get user statistics
    
    Requires: SYSTEM_READ permission
    """
    
    stats = api_analytics.get_user_stats(user_id, limit)
    
    return stats


@router.get("/analytics/errors")
@require_permission(Permission.SYSTEM_READ)
async def get_error_analytics(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get error statistics
    
    Requires: SYSTEM_READ permission
    """
    
    stats = api_analytics.get_error_stats(limit)
    
    return stats


@router.get("/analytics/status-codes")
@require_permission(Permission.SYSTEM_READ)
async def get_status_code_analytics(
    current_user: dict = Depends(get_current_user)
):
    """
    Get HTTP status code distribution
    
    Requires: SYSTEM_READ permission
    """
    
    stats = api_analytics.get_status_code_stats()
    
    return stats


@router.post("/analytics/reset")
@require_permission(Permission.SYSTEM_ADMIN)
async def reset_analytics(
    current_user: dict = Depends(get_current_user)
):
    """
    Reset analytics data
    
    Requires: SYSTEM_ADMIN permission
    """
    
    api_analytics.reset()
    
    return {
        "message": "Analytics data reset"
    }
```

---

**Продолжение следует...**

Создано:
- ✅ Advanced Rate Limiter (multi-tier, sliding window)
- ✅ Circuit Breaker (fault tolerance)
- ✅ Request Router (load balancing)
- ✅ API Analytics (monitoring)
- ✅ Gateway Middleware
- ✅ API Routes

**Следующие файлы:**
- Tests
- Docker configuration
- Documentation
- Week summary

**Готовы продолжить?**