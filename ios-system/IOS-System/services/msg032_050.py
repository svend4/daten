"""
Redis caching layer
"""

import redis.asyncio as redis
import json
import pickle
from typing import Optional, Any
from functools import wraps
import hashlib

from .config import settings


class CacheManager:
    """Redis cache manager"""
    
    def __init__(self):
        self.redis = None
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis:
            self.redis = await redis.from_url(
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=False
            )
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self.connect()
        
        value = await self.redis.get(key)
        if value:
            return pickle.loads(value)
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        await self.connect()
        
        serialized = pickle.dumps(value)
        await self.redis.set(key, serialized, ex=ttl)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        await self.connect()
        await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        await self.connect()
        
        keys = []
        async for key in self.redis.scan_iter(pattern):
            keys.append(key)
        
        if keys:
            await self.redis.delete(*keys)


# Global cache instance
cache = CacheManager()


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=600, key_prefix="search")
        async def search_documents(query: str):
            ...
    """
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            
            # Add arguments to key
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
            
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float)):
                    key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator