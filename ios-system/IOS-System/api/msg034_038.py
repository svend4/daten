"""
Role-Based Access Control
"""

from enum import Enum
from typing import List, Set
from functools import wraps
from fastapi import HTTPException, status


class Permission(Enum):
    """System permissions"""
    
    # Document permissions
    DOCUMENT_CREATE = "document:create"
    DOCUMENT_READ = "document:read"
    DOCUMENT_UPDATE = "document:update"
    DOCUMENT_DELETE = "document:delete"
    
    # Domain permissions
    DOMAIN_CREATE = "domain:create"
    DOMAIN_READ = "domain:read"
    DOMAIN_UPDATE = "domain:update"
    DOMAIN_DELETE = "domain:delete"
    
    # Admin permissions
    ADMIN_USERS = "admin:users"
    ADMIN_SYSTEM = "admin:system"


class Role(Enum):
    """System roles"""
    
    VIEWER = "viewer"
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


# Role-Permission mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.DOCUMENT_READ,
        Permission.DOMAIN_READ,
    },
    Role.CONTRIBUTOR: {
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOMAIN_READ,
    },
    Role.ADMIN: {
        Permission.DOCUMENT_CREATE,
        Permission.DOCUMENT_READ,
        Permission.DOCUMENT_UPDATE,
        Permission.DOCUMENT_DELETE,
        Permission.DOMAIN_CREATE,
        Permission.DOMAIN_READ,
        Permission.DOMAIN_UPDATE,
        Permission.ADMIN_USERS,
    },
    Role.SUPERADMIN: set(Permission),  # All permissions
}


class RBACManager:
    """RBAC manager"""
    
    @staticmethod
    def has_permission(user_role: str, permission: Permission) -> bool:
        """Check if role has permission"""
        try:
            role = Role(user_role)
            return permission in ROLE_PERMISSIONS[role]
        except (ValueError, KeyError):
            return False
    
    @staticmethod
    def get_user_permissions(user_role: str) -> Set[Permission]:
        """Get all permissions for role"""
        try:
            role = Role(user_role)
            return ROLE_PERMISSIONS[role]
        except ValueError:
            return set()


def require_permission(permission: Permission):
    """Decorator to require permission"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: dict, **kwargs):
            user_role = current_user.get('role', 'viewer')
            
            if not RBACManager.has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, current_user=current_user, **kwargs)
        
        return wrapper
    return decorator