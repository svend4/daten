"""
Webhook Management Routes
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from ios_core.events.webhook_manager import webhook_manager
from ios_core.events.models import EventType
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class CreateWebhookRequest(BaseModel):
    name: str
    url: HttpUrl
    event_types: List[EventType]
    secret: Optional[str] = None


class UpdateWebhookRequest(BaseModel):
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    event_types: Optional[List[EventType]] = None
    is_active: Optional[bool] = None


@router.post("/webhooks")
async def create_webhook(
    request: CreateWebhookRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create webhook subscription
    
    Subscribe to events via HTTP callbacks.
    """
    
    subscription = await webhook_manager.create_subscription(
        user_id=current_user["user_id"],
        name=request.name,
        url=str(request.url),
        event_types=request.event_types,
        secret=request.secret
    )
    
    return {
        "id": subscription.id,
        "name": subscription.name,
        "url": subscription.url,
        "event_types": subscription.event_types,
        "secret": subscription.secret,
        "is_active": subscription.is_active,
        "created_at": subscription.created_at.isoformat()
    }


@router.get("/webhooks")
async def list_webhooks(
    current_user: dict = Depends(get_current_user)
):
    """
    List user's webhook subscriptions
    """
    
    subscriptions = await webhook_manager.get_subscriptions(
        user_id=current_user["user_id"]
    )
    
    return {
        "webhooks": [
            {
                "id": sub.id,
                "name": sub.name,
                "url": sub.url,
                "event_types": sub.event_types,
                "is_active": sub.is_active,
                "total_deliveries": sub.total_deliveries,
                "successful_deliveries": sub.successful_deliveries,
                "failed_deliveries": sub.failed_deliveries,
                "last_delivery_at": sub.last_delivery_at.isoformat()
                    if sub.last_delivery_at else None
            }
            for sub in subscriptions
        ],
        "total": len(subscriptions)
    }


@router.get("/webhooks/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get webhook details
    """
    
    subscriptions = await webhook_manager.get_subscriptions(
        user_id=current_user["user_id"]
    )
    
    subscription = next(
        (s for s in subscriptions if s.id == webhook_id),
        None
    )
    
    if not subscription:
        raise HTTPException(404, "Webhook not found")
    
    return {
        "id": subscription.id,
        "name": subscription.name,
        "url": subscription.url,
        "event_types": subscription.event_types,
        "secret": subscription.secret,
        "is_active": subscription.is_active,
        "retry_count": subscription.retry_count,
        "timeout_seconds": subscription.timeout_seconds,
        "total_deliveries": subscription.total_deliveries,
        "successful_deliveries": subscription.successful_deliveries,
        "failed_deliveries": subscription.failed_deliveries,
        "last_delivery_at": subscription.last_delivery_at.isoformat()
            if subscription.last_delivery_at else None,
        "last_error": subscription.last_error,
        "created_at": subscription.created_at.isoformat()
    }


@router.patch("/webhooks/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update webhook subscription
    """
    
    # Verify ownership
    subscriptions = await webhook_manager.get_subscriptions(
        user_id=current_user["user_id"]
    )
    
    if not any(s.id == webhook_id for s in subscriptions):
        raise HTTPException(404, "Webhook not found")
    
    # Prepare updates
    updates = {}
    
    if request.name is not None:
        updates["name"] = request.name
    
    if request.url is not None:
        updates["url"] = str(request.url)
    
    if request.event_types is not None:
        updates["event_types"] = [et.value for et in request.event_types]
    
    if request.is_active is not None:
        updates["is_active"] = request.is_active
    
    # Update
    subscription = await webhook_manager.update_subscription(
        webhook_id,
        **updates
    )
    
    return {
        "id": subscription.id,
        "name": subscription.name,
        "url": subscription.url,
        "event_types": subscription.event_types,
        "is_active": subscription.is_active
    }


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete webhook subscription
    """
    
    # Verify ownership
    subscriptions = await webhook_manager.get_subscriptions(
        user_id=current_user["user_id"]
    )
    
    if not any(s.id == webhook_id for s in subscriptions):
        raise HTTPException(404, "Webhook not found")
    
    # Delete
    success = await webhook_manager.delete_subscription(webhook_id)
    
    if not success:
        raise HTTPException(500, "Failed to delete webhook")
    
    return {"message": "Webhook deleted"}


@router.get("/webhooks/{webhook_id}/deliveries")
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get webhook delivery history
    """
    
    # Verify ownership
    subscriptions = await webhook_manager.get_subscriptions(
        user_id=current_user["user_id"]
    )
    
    if not any(s.id == webhook_id for s in subscriptions):
        raise HTTPException(404, "Webhook not found")
    
    # Get deliveries
    deliveries = await webhook_manager.get_delivery_history(
        webhook_id,
        limit=limit
    )
    
    return {
        "deliveries": [
            {
                "id": d.id,
                "event_type": d.event_type,
                "success": d.success,
                "response_status": d.response_status,
                "response_time_ms": d.response_time_ms,
                "attempt_number": d.attempt_number,
                "error_message": d.error_message,
                "created_at": d.created_at.isoformat(),
                "delivered_at": d.delivered_at.isoformat()
                    if d.delivered_at else None
            }
            for d in deliveries
        ],
        "total": len(deliveries)
    }


@router.get("/event-types")
async def list_event_types():
    """
    List available event types for webhooks
    """
    
    return {
        "event_types": [
            {
                "value": et.value,
                "category": et.value.split(".")[0]
            }
            for et in EventType
        ]
    }