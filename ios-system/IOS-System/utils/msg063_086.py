"""
Intelligent Caching System
"""

import logging
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta
import asyncio

import redis.asyncio as redis

from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Advanced caching with Redis
    
    Features:
    - TTL-based expiration
    - LRU eviction
    - Cache invalidation
    - Hit/miss tracking
    - Automatic serialization
    
    Usage:
        cache = CacheManager()
        
        # Cache result
        @cache.cached(ttl=3600)
        async def expensive_operation(arg):
            ...
    """
    
    def __init__(self):
        self.redis_client = None
        self.hits = 0
        self.misses = 0
        self.local_cache = {}
        self.local_cache_size = 100
    
    async def initialize(self):
        """Initialize Redis connection"""
        
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Cache manager initialized (Redis)")
        except Exception as e:
            logger.warning(f"Redis not available, using local cache: {e}")
            self.redis_client = None
    
    def cached(
        self,
        ttl: int = 3600,
        key_prefix: str = ""
    ):
        """
        Decorator for caching function results
        
        Args:
            ttl: Time to live in seconds
            key_prefix: Cache key prefix
        """
        
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(
                    key_prefix or func.__name__,
                    args,
                    kwargs
                )
                
                # Try to get from cache
                cached_value = await self.get(cache_key)
                
                if cached_value is not None:
                    self.hits += 1
                    logger.debug(f"Cache hit: {cache_key}")
                    return cached_value
                
                # Cache miss - compute value
                self.misses += 1
                logger.debug(f"Cache miss: {cache_key}")
                
                result = await func(*args, **kwargs)
                
                # Store in cache
                await self.set(cache_key, result, ttl=ttl)
                
                return result
            
            return wrapper
        return decorator
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        
        if self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        # Fallback to local cache
        return self.local_cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """Set value in cache"""
        
        serialized = json.dumps(value, default=str)
        
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    key,
                    ttl,
                    serialized
                )
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        # Fallback to local cache
        if len(self.local_cache) >= self.local_cache_size:
            # Remove oldest
            oldest = next(iter(self.local_cache))
            del self.local_cache[oldest]
        
        self.local_cache[key] = json.loads(serialized)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        if key in self.local_cache:
            del self.local_cache[key]
    
    async def clear(self, pattern: str = "*"):
        """Clear cache by pattern"""
        
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache keys")
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        else:
            self.local_cache.clear()
    
    def _generate_key(
        self,
        prefix: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate cache key from function arguments"""
        
        # Create deterministic string from arguments
        key_parts = [prefix]
        
        # Add positional args
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            else:
                key_parts.append(hashlib.md5(
                    str(arg).encode()
                ).hexdigest()[:8])
        
        # Add keyword args
        for k, v in sorted(kwargs.items()):
            if isinstance(v, (str, int, float, bool)):
                key_parts.append(f"{k}:{v}")
            else:
                key_parts.append(f"{k}:{hashlib.md5(str(v).encode()).hexdigest()[:8]}")
        
        return ":".join(key_parts)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "backend": "redis" if self.redis_client else "local",
            "local_cache_size": len(self.local_cache)
        }


# Global cache manager
cache_manager = CacheManager()