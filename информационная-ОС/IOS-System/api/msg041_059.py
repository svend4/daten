"""
Observability middleware for FastAPI
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ios_core.observability import metrics, get_logger

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for capturing metrics and logs
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        logger.info(
            "HTTP request started",
            method=method,
            path=path,
            ip=client_ip,
            user_agent=user_agent
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics.record_http_request(
                method=method,
                endpoint=path,
                status=response.status_code,
                duration=duration
            )
            
            # Log response
            logger.info(
                "HTTP request completed",
                method=method,
                path=path,
                status=response.status_code,
                duration=duration,
                ip=client_ip
            )
            
            # Add response headers
            response.headers["X-Request-Duration"] = str(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record error metrics
            metrics.record_http_request(
                method=method,
                endpoint=path,
                status=500,
                duration=duration
            )
            
            # Log error
            logger.error(
                "HTTP request failed",
                method=method,
                path=path,
                error=str(e),
                duration=duration,
                ip=client_ip,
                exc_info=True
            )
            
            raise