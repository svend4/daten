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