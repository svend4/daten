"""
Middleware for automatic audit logging
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ios_core.security.audit_log import audit_logger, AuditAction, AuditSeverity

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Automatically log all API requests
    """
    
    # Actions to audit
    AUDIT_ACTIONS = {
        ("POST", "/api/auth/token"): AuditAction.LOGIN_SUCCESS,
        ("POST", "/api/auth/logout"): AuditAction.LOGOUT,
        ("POST", "/api/documents/upload"): AuditAction.DOCUMENT_CREATE,
        ("GET", "/api/documents/{id}"): AuditAction.DOCUMENT_READ,
        ("PUT", "/api/documents/{id}"): AuditAction.DOCUMENT_UPDATE,
        ("DELETE", "/api/documents/{id}"): AuditAction.DOCUMENT_DELETE,
        ("POST", "/api/search"): AuditAction.SEARCH_EXECUTE,
        ("POST", "/api/data/export"): AuditAction.DATA_EXPORT,
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Get user info if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("username")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Determine if should audit
            action = self._get_audit_action(method, path)
            
            if action:
                # Log successful request
                await audit_logger.log(
                    action=action,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_id=request.headers.get("x-request-id"),
                    success=response.status_code < 400,
                    duration_ms=duration_ms,
                    severity=self._get_severity(response.status_code)
                )
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log failed request
            action = self._get_audit_action(method, path)
            
            if action:
                await audit_logger.log(
                    action=action,
                    user_id=user_id,
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    request_id=request.headers.get("x-request-id"),
                    success=False,
                    error_message=str(e),
                    duration_ms=duration_ms,
                    severity=AuditSeverity.ERROR
                )
            
            raise
    
    def _get_audit_action(self, method: str, path: str) -> Optional[AuditAction]:
        """Determine audit action for request"""
        
        # Check exact match
        key = (method, path)
        if key in self.AUDIT_ACTIONS:
            return self.AUDIT_ACTIONS[key]
        
        # Check pattern match (simple implementation)
        for (m, p), action in self.AUDIT_ACTIONS.items():
            if method == m and self._path_matches(path, p):
                return action
        
        return None
    
    def _path_matches(self, path: str, pattern: str) -> bool:
        """Simple path pattern matching"""
        
        path_parts = path.split("/")
        pattern_parts = pattern.split("/")
        
        if len(path_parts) != len(pattern_parts):
            return False
        
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            if pattern_part.startswith("{") and pattern_part.endswith("}"):
                continue  # Wildcard
            if path_part != pattern_part:
                return False
        
        return True
    
    def _get_severity(self, status_code: int) -> AuditSeverity:
        """Determine severity from status code"""
        
        if status_code >= 500:
            return AuditSeverity.ERROR
        elif status_code >= 400:
            return AuditSeverity.WARNING
        else:
            return AuditSeverity.INFO