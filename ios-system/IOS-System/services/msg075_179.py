"""
SDK Models
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Document:
    """Document model"""
    
    id: str
    title: str
    content: str
    domain_id: Optional[str] = None
    metadata: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Document":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            domain_id=data.get("domain_id"),
            metadata=data.get("metadata"),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at"))
        )
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string"""
        
        if not dt_str:
            return None
        
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except:
            return None


@dataclass
class SearchResult:
    """Search result model"""
    
    document_id: str
    title: str
    content: str
    score: float
    highlight: Optional[str] = None
    metadata: Optional[Dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "SearchResult":
        """Create from API response"""
        
        return cls(
            document_id=data["document_id"],
            title=data["title"],
            content=data.get("content", ""),
            score=data["score"],
            highlight=data.get("highlight"),
            metadata=data.get("metadata")
        )


@dataclass
class User:
    """User model"""
    
    id: str
    email: str
    username: str
    is_active: bool
    roles: List[str]
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            email=data["email"],
            username=data["username"],
            is_active=data.get("is_active", True),
            roles=data.get("roles", []),
            created_at=Document._parse_datetime(data.get("created_at"))
        )


@dataclass
class Webhook:
    """Webhook model"""
    
    id: str
    name: str
    url: str
    event_types: List[str]
    is_active: bool
    secret: Optional[str] = None
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Webhook":
        """Create from API response"""
        
        return cls(
            id=data["id"],
            name=data["name"],
            url=data["url"],
            event_types=data.get("event_types", []),
            is_active=data.get("is_active", True),
            secret=data.get("secret"),
            created_at=Document._parse_datetime(data.get("created_at"))
        )