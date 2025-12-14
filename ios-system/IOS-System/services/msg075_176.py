"""
IOS System Python SDK
Official Python client for IOS API

Installation:
    pip install ios-sdk

Usage:
    from ios_sdk import IOSClient
    
    client = IOSClient(api_key="your_key")
    
    # Create document
    doc = client.documents.create(
        title="My Document",
        content="Content here"
    )
    
    # Search
    results = client.search.query("personal budget")
"""

from .client import IOSClient
from .exceptions import (
    IOSError,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)
from .models import Document, SearchResult, User

__version__ = "1.0.0"

__all__ = [
    'IOSClient',
    'IOSError',
    'AuthenticationError',
    'RateLimitError',
    'NotFoundError',
    'Document',
    'SearchResult',
    'User',
]