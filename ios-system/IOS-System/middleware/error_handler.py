"""
Error Handler Middleware - Централизованная обработка ошибок
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from typing import Dict, Any
import time

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware для централизованной обработки ошибок
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
            
        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Validation Error",
                    "message": str(e),
                    "type": "validation_error"
                }
            )
            
        except PermissionError as e:
            logger.warning(f"Permission denied: {e}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Permission Denied",
                    "message": str(e),
                    "type": "permission_error"
                }
            )
            
        except FileNotFoundError as e:
            logger.warning(f"Resource not found: {e}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "message": str(e),
                    "type": "not_found_error"
                }
            )
            
        except TimeoutError as e:
            logger.error(f"Timeout error: {e}")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Timeout",
                    "message": "Request timed out",
                    "type": "timeout_error"
                }
            )
            
        except ConnectionError as e:
            logger.error(f"Connection error: {e}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service Unavailable",
                    "message": "External service unavailable",
                    "type": "connection_error"
                }
            )
            
        except Exception as e:
            # Логируем полный traceback
            logger.error(f"Unhandled exception: {e}")
            logger.error(traceback.format_exc())
            
            # В production не показываем детали ошибки
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": "internal_error",
                    "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None
                }
            )
