"""
Multi-Level Caching System
L1: In-memory (LRU) -> L2: Redis -> L3: Database

Features:
- Automatic cache warming
- Cache invalidation strategies
- Cache stampede prevention
- TTL management
- Cache statistics
"""

import logging
import hashlib
import pickle
import time
from typing import Any, Optional, Callable, Dict
from functools import wraps
from datetime import datetime, timedelta
from collections import OrderedDict

import redis
from redis.lock import Lock

from ..config import settings

logger = logging.getLogger(__name__)


class LRUCache:
    """
    In-memory LRU (Least Recently Used) cache
    
    L1 cache - fastest, limited capacity
    """
    
    def __init__(self, capacity: int = 1000):
        self.cache = OrderedDict()
        self.capacity = capacity
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        
        value, expires_at = self.cache[key]
        
        # Check expiration
        if expires_at and time.time() > expires_at:
            del self.cache[key]
            return None
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        
        # Remove oldest if at capacity
        if len(self.cache) >= self.capacity:
            self.cache.popitem(last=False)
        
        self.cache[key] = (value, expires_at)
        self.cache.move_to_end(key)
    
    def delete(self, key: str):
        """Delete from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            "size": len(self.cache),
            "capacity": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2)
        }


class RedisCache:
    """
    Redis-based distributed cache
    
    L2 cache - shared across instances
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "cache:"
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = self.redis.get(self._make_key(key))
            if value:
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in Redis"""
        try:
            serialized = pickle.dumps(value)
            
            if ttl:
                self.redis.setex(
                    self._make_key(key),
                    ttl,
                    serialized
                )
            else:
                self.redis.set(
                    self._make_key(key),
                    serialized
                )
        except Exception as e:
            logger.error(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """Delete from Redis"""
        try:
            self.redis.delete(self._make_key(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
    
    def delete_pattern(self, pattern: str):
        """Delete keys matching pattern"""
        try:
            keys = self.redis.keys(self._make_key(pattern))
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis delete pattern error: {e}")
    
    def clear(self):
        """Clear all cache entries"""
        try:
            keys = self.redis.keys(f"{self.prefix}*")
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
    
    def stats(self) -> Dict:
        """Get Redis cache statistics"""
        try:
            info = self.redis.info("stats")
            return {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0)
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {}


class MultiLevelCache:
    """
    Multi-level caching system
    
    Automatically manages L1 (memory) and L2 (Redis) caches
    """
    
    def __init__(
        self,
        redis_client: redis.Redis,
        l1_capacity: int = 1000
    ):
        self.l1 = LRUCache(capacity=l1_capacity)
        self.l2 = RedisCache(redis_client)
        self.redis = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Checks L1 first, then L2, promotes to L1 on L2 hit
        """
        # Try L1 (memory)
        value = self.l1.get(key)
        if value is not None:
            logger.debug(f"L1 cache hit: {key}")
            return value
        
        # Try L2 (Redis)
        value = self.l2.get(key)
        if value is not None:
            logger.debug(f"L2 cache hit: {key}")
            # Promote to L1
            self.l1.set(key, value, ttl=300)  # 5 min in L1
            return value
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        l1_only: bool = False
    ):
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            l1_only: Only cache in L1 (memory)
        """
        # Always set in L1
        self.l1.set(key, value, ttl=min(ttl, 300) if ttl else 300)
        
        # Set in L2 unless l1_only
        if not l1_only:
            self.l2.set(key, value, ttl=ttl)
        
        logger.debug(f"Cache set: {key} (L1{'only' if l1_only else ' + L2'})")
    
    def delete(self, key: str):
        """Delete from all cache levels"""
        self.l1.delete(key)
        self.l2.delete(key)
        logger.debug(f"Cache deleted: {key}")
    
    def delete_pattern(self, pattern: str):
        """Delete keys matching pattern from all levels"""
        # L1 doesn't support pattern deletion efficiently
        self.l1.clear()  # Clear all L1
        self.l2.delete_pattern(pattern)
        logger.debug(f"Cache pattern deleted: {pattern}")
    
    def clear(self):
        """Clear all cache levels"""
        self.l1.clear()
        self.l2.clear()
        logger.info("All caches cleared")
    
    def stats(self) -> Dict:
        """Get statistics for all cache levels"""
        return {
            "l1": self.l1.stats(),
            "l2": self.l2.stats()
        }
    
    def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None,
        lock_timeout: int = 10
    ) -> Any:
        """
        Get from cache or compute and set
        
        Prevents cache stampede using distributed lock
        """
        # Try cache first
        value = self.get(key)
        if value is not None:
            return value
        
        # Acquire lock to prevent stampede
        lock_key = f"lock:{key}"
        lock = Lock(
            self.redis,
            lock_key,
            timeout=lock_timeout,
            blocking_timeout=5
        )
        
        try:
            if lock.acquire(blocking=True):
                # Double-check cache (another process might have set it)
                value = self.get(key)
                if value is not None:
                    return value
                
                # Compute value
                logger.debug(f"Cache miss, computing: {key}")
                value = factory()
                
                # Store in cache
                self.set(key, value, ttl=ttl)
                
                return value
        finally:
            try:
                lock.release()
            except:
                pass
        
        # Fallback if lock acquisition fails
        logger.warning(f"Failed to acquire lock for {key}, computing anyway")
        return factory()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=600, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).get(user_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and args
                key_parts = [
                    key_prefix or func.__name__,
                    str(args),
                    str(sorted(kwargs.items()))
                ]
                cache_key = hashlib.md5(
                    "".join(key_parts).encode()
                ).hexdigest()
            
            # Get cache instance (assumes it's available)
            from ..dependencies import get_cache
            cache = get_cache()
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        return wrapper
    return decorator


class CacheWarmer:
    """
    Preemptively warms cache with frequently accessed data
    """
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
    
    async def warm_popular_documents(self, limit: int = 100):
        """Warm cache with most popular documents"""
        from ..database.session import get_session
        from ..models import Document
        
        logger.info(f"Warming cache with top {limit} documents")
        
        async with get_session() as session:
            # Get most accessed documents
            query = """
                SELECT id, title, content
                FROM documents
                ORDER BY view_count DESC
                LIMIT :limit
            """
            
            result = await session.execute(query, {"limit": limit})
            
            for row in result:
                cache_key = f"document:{row.id}"
                self.cache.set(
                    cache_key,
                    {
                        "id": row.id,
                        "title": row.title,
                        "content": row.content
                    },
                    ttl=3600  # 1 hour
                )
        
        logger.info("Cache warming completed")
    
    async def warm_search_results(self, queries: list[str]):
        """Warm cache with common search queries"""
        from ..search.search_service import SearchService
        
        logger.info(f"Warming cache with {len(queries)} search queries")
        
        search_service = SearchService()
        
        for query in queries:
            cache_key = f"search:{hashlib.md5(query.encode()).hexdigest()}"
            
            try:
                results = await search_service.search(query, limit=20)
                self.cache.set(cache_key, results, ttl=1800)  # 30 min
            except Exception as e:
                logger.error(f"Failed to warm search cache for '{query}': {e}")
        
        logger.info("Search cache warming completed")
    
    async def warm_user_data(self, user_ids: list[int]):
        """Warm cache with user data"""
        from ..database.session import get_session
        from ..models import User
        
        logger.info(f"Warming cache with {len(user_ids)} users")
        
        async with get_session() as session:
            for user_id in user_ids:
                user = await session.get(User, user_id)
                if user:
                    cache_key = f"user:{user_id}"
                    self.cache.set(
                        cache_key,
                        user.to_dict(),
                        ttl=3600
                    )
        
        logger.info("User cache warming completed")


class CacheInvalidator:
    """
    Handles cache invalidation strategies
    """
    
    def __init__(self, cache: MultiLevelCache):
        self.cache = cache
    
    def invalidate_document(self, document_id: int):
        """Invalidate all caches related to a document"""
        patterns = [
            f"document:{document_id}",
            f"document:{document_id}:*",
            f"search:*",  # Invalidate all searches (could be optimized)
            "documents:list:*"
        ]
        
        for pattern in patterns:
            self.cache.delete_pattern(pattern)
        
        logger.info(f"Invalidated cache for document {document_id}")
    
    def invalidate_user(self, user_id: int):
        """Invalidate all caches related to a user"""
        patterns = [
            f"user:{user_id}",
            f"user:{user_id}:*",
            f"user_documents:{user_id}:*"
        ]
        
        for pattern in patterns:
            self.cache.delete_pattern(pattern)
        
        logger.info(f"Invalidated cache for user {user_id}")
    
    def invalidate_search(self):
        """Invalidate all search result caches"""
        self.cache.delete_pattern("search:*")
        logger.info("Invalidated all search caches")
    
    def invalidate_all(self):
        """Invalidate entire cache (use with caution)"""
        self.cache.clear()
        logger.warning("Invalidated ALL caches")


# Global cache instance
_cache_instance: Optional[MultiLevelCache] = None


def init_cache(redis_client: redis.Redis) -> MultiLevelCache:
    """Initialize global cache instance"""
    global _cache_instance
    _cache_instance = MultiLevelCache(redis_client)
    return _cache_instance


def get_cache() -> MultiLevelCache:
    """Get global cache instance"""
    if _cache_instance is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first.")
    return _cache_instance