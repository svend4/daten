"""
SDK Exceptions
"""

from typing import Optional


class IOSError(Exception):
    """Base exception for IOS SDK"""
    pass


class AuthenticationError(IOSError):
    """Authentication failed"""
    pass


class RateLimitError(IOSError):
    """Rate limit exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[str] = None):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(IOSError):
    """Resource not found"""
    pass


class ValidationError(IOSError):
    """Validation error"""
    pass


class ServerError(IOSError):
    """Server error"""
    pass