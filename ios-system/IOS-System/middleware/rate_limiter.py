"""
Rate Limiter Middleware - Ограничение частоты запросов
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from typing import Optional, Callable
import time

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware для ограничения частоты запросов (rate limiting)
    Использует Redis для хранения счетчиков
    """
    
    def __init__(
        self,
        app,
        redis_cache=None,
        requests_per_minute: int = 60,
        enabled: bool = True
    ):
        super().__init__(app)
        self.redis_cache = redis_cache
        self.requests_per_minute = requests_per_minute
        self.enabled = enabled
        self.window_seconds = 60
        
    async def dispatch(self, request: Request, call_next: Callable):
        # Пропускаем если rate limiting выключен
        if not self.enabled or not self.redis_cache:
            return await call_next(request)
            
        # Пропускаем health check и metrics endpoints
        if request.url.path in ['/health', '/metrics', '/']:
            return await call_next(request)
            
        # Получаем идентификатор клиента
        client_id = self._get_client_id(request)
        
        # Проверяем rate limit
        allowed, remaining, reset_time = await self._check_rate_limit(client_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Max {self.requests_per_minute} requests per minute.",
                    "retry_after": reset_time
                }
            )
            
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Добавляем rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)
        
        return response
        
    def _get_client_id(self, request: Request) -> str:
        """
        Получение идентификатора клиента
        Использует API key если есть, иначе IP адрес
        """
        # Проверяем API key в заголовках
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
            
        # Проверяем authenticated user
        if hasattr(request.state, 'user') and request.state.user:
            return f"user:{request.state.user.id}"
            
        # Fallback на IP адрес
        if request.client:
            return f"ip:{request.client.host}"
            
        return "unknown"
        
    async def _check_rate_limit(self, client_id: str) -> tuple[bool, int, int]:
        """
        Проверка rate limit для клиента
        
        Returns:
            (allowed, remaining_requests, reset_time_unix)
        """
        try:
            # Ключ для Redis
            key = f"rate_limit:{client_id}"
            
            # Получаем текущее количество запросов
            current = await self.redis_cache.get(key)
            
            if current is None:
                # Первый запрос в окне
                await self.redis_cache.set(key, 1, ex=self.window_seconds)
                reset_time = int(time.time()) + self.window_seconds
                return True, self.requests_per_minute - 1, reset_time
                
            current = int(current)
            
            if current >= self.requests_per_minute:
                # Лимит превышен
                ttl = await self.redis_cache.ttl(key)
                reset_time = int(time.time()) + max(ttl, 0)
                return False, 0, reset_time
                
            # Инкрементируем счетчик
            new_count = await self.redis_cache.incr(key)
            
            ttl = await self.redis_cache.ttl(key)
            reset_time = int(time.time()) + max(ttl, 0)
            remaining = max(self.requests_per_minute - new_count, 0)
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # В случае ошибки пропускаем запрос
            return True, self.requests_per_minute, int(time.time()) + self.window_seconds
