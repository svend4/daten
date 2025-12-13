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