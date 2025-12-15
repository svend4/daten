"""
Rate limiting middleware
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
from threading import Lock

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    async def dispatch(self, request: Request, call_next):
        # Get client identifier (IP or user)
        client_id = request.client.host
        
        # Check rate limit
        if not self._is_allowed(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self._get_remaining(client_id)
        )
        
        return response
    
    def _is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed"""
        with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                return False
            
            # Add new request
            self.requests[client_id].append(now)
            return True
    
    def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests"""
        return max(0, self.requests_per_minute - len(self.requests[client_id]))