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