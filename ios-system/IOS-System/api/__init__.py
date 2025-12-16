"""
API modules for IOS System
"""
from .routes import (
    auth_router,
    documents_router,
    search_router,
    graph_router,
    admin_router,
    ai_router,
)

__all__ = [
    'auth_router',
    'documents_router',
    'search_router',
    'graph_router',
    'admin_router',
    'ai_router',
]
