"""
Request Logger Middleware - Логирование всех HTTP запросов
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import time
import uuid
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware для логирования всех HTTP запросов
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Генерируем уникальный ID для запроса
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Засекаем время начала
        start_time = time.time()
        
        # Логируем входящий запрос
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}] from {request.client.host if request.client else 'unknown'}"
        )
        
        # Обрабатываем запрос
        response = await call_next(request)
        
        # Вычисляем время обработки
        process_time = time.time() - start_time
        process_time_ms = round(process_time * 1000, 2)
        
        # Добавляем заголовки с метриками
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time_ms)
        
        # Логируем завершение запроса
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[{request_id}] {response.status_code} in {process_time_ms}ms"
        )
        
        return response
