"""
Event System Models
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import Column, String, Integer, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..database import Base


class EventType(str, Enum):
    """Event types"""
    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"
    DOCUMENT_VIEWED = "document.viewed"
    
    # Search events
    SEARCH_PERFORMED = "search.performed"
    SEARCH_RESULT_CLICKED = "search.result_clicked"
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Security events
    SECURITY_BREACH_DETECTED = "security.breach_detected"
    MFA_ENABLED = "security.mfa_enabled"
    PASSWORD_CHANGED = "security.password_changed"
    
    # System events
    SYSTEM_STARTED = "system.started"
    SYSTEM_ERROR = "system.error"
    BACKUP_COMPLETED = "system.backup_completed"
    
    # AI/ML events
    EMBEDDING_CREATED = "ml.embedding_created"
    GPT_GENERATION_COMPLETED = "ml.gpt_generation_completed"
    
    # Integration events
    WEBHOOK_DELIVERED = "integration.webhook_delivered"
    WEBHOOK_FAILED = "integration.webhook_failed"


class Event(BaseModel):
    """
    Event model
    
    Represents a system event that can be:
    - Published to event bus
    - Stored in event store
    - Delivered via webhooks
    """
    
    id: Optional[str] = None
    type: EventType
    source: str  # Service/component that generated event
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None  # For tracing related events
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class WebhookSubscription(Base):
    """
    Webhook subscription
    
    Allows external systems to receive events via HTTP callbacks.
    """
    
    __tablename__ = "webhook_subscriptions"
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100))  # For signature verification
    
    # Event filtering
    event_types = Column(JSON)  # List of EventType values
    
    # Configuration
    is_active = Column(Boolean, default=True)
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    
    # Statistics
    total_deliveries = Column(Integer, default=0)
    successful_deliveries = Column(Integer, default=0)
    failed_deliveries = Column(Integer, default=0)
    last_delivery_at = Column(DateTime)
    last_error = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="webhook_subscriptions")
    deliveries = relationship("WebhookDelivery", back_populates="subscription")


class WebhookDelivery(Base):
    """
    Webhook delivery attempt
    
    Tracks individual webhook deliveries for debugging and monitoring.
    """
    
    __tablename__ = "webhook_deliveries"
    
    id = Column(String(50), primary_key=True)
    subscription_id = Column(String(50), ForeignKey("webhook_subscriptions.id"))
    event_id = Column(String(50))
    event_type = Column(String(100))
    
    # Request
    request_url = Column(String(500))
    request_payload = Column(JSON)
    request_headers = Column(JSON)
    
    # Response
    response_status = Column(Integer)
    response_body = Column(Text)
    response_time_ms = Column(Integer)
    
    # Status
    success = Column(Boolean)
    error_message = Column(Text)
    attempt_number = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime)
    
    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")