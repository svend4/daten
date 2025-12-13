"""
Webhook Manager - External event delivery
"""

import logging
from typing import Dict, List, Optional
import asyncio
import hashlib
import hmac
import time
from datetime import datetime
import uuid

import httpx

from .models import Event, EventType, WebhookSubscription, WebhookDelivery
from ..database import async_session
from sqlalchemy import select, update

logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Webhook delivery manager
    
    Features:
    - Async HTTP delivery
    - Retry with exponential backoff
    - Signature verification (HMAC)
    - Delivery tracking
    - Circuit breaker integration
    - Batch processing
    
    Usage:
        manager = WebhookManager()
        
        # Create subscription
        sub = await manager.create_subscription(
            user_id="user123",
            name="My Webhook",
            url="https://example.com/webhook",
            event_types=[EventType.DOCUMENT_CREATED]
        )
        
        # Deliver event
        await manager.deliver_event(event)
    """
    
    def __init__(self, max_retries: int = 3, timeout: int = 30):
        self.max_retries = max_retries
        self.timeout = timeout
        self.delivery_queue = asyncio.Queue()
        self.is_running = False
    
    async def create_subscription(
        self,
        user_id: str,
        name: str,
        url: str,
        event_types: List[EventType],
        secret: Optional[str] = None
    ) -> WebhookSubscription:
        """
        Create webhook subscription
        
        Args:
            user_id: User ID
            name: Subscription name
            url: Webhook URL
            event_types: Event types to receive
            secret: Optional secret for HMAC signatures
        
        Returns:
            Created subscription
        """
        
        async with async_session() as session:
            # Generate secret if not provided
            if not secret:
                secret = str(uuid.uuid4())
            
            subscription = WebhookSubscription(
                id=f"wh_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                name=name,
                url=url,
                secret=secret,
                event_types=[et.value for et in event_types],
                is_active=True
            )
            
            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)
            
            logger.info(f"Created webhook subscription: {subscription.id}")
            
            return subscription
    
    async def update_subscription(
        self,
        subscription_id: str,
        **updates
    ) -> Optional[WebhookSubscription]:
        """
        Update webhook subscription
        
        Args:
            subscription_id: Subscription ID
            **updates: Fields to update
        
        Returns:
            Updated subscription or None
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            for key, value in updates.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            
            subscription.updated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(subscription)
            
            logger.info(f"Updated webhook subscription: {subscription_id}")
            
            return subscription
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Delete webhook subscription
        
        Args:
            subscription_id: Subscription ID
        
        Returns:
            True if deleted
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return False
            
            await session.delete(subscription)
            await session.commit()
            
            logger.info(f"Deleted webhook subscription: {subscription_id}")
            
            return True
    
    async def get_subscriptions(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        active_only: bool = True
    ) -> List[WebhookSubscription]:
        """
        Get webhook subscriptions
        
        Args:
            user_id: Filter by user
            event_type: Filter by event type
            active_only: Only active subscriptions
        
        Returns:
            List of subscriptions
        """
        
        async with async_session() as session:
            query = select(WebhookSubscription)
            
            if user_id:
                query = query.where(WebhookSubscription.user_id == user_id)
            
            if active_only:
                query = query.where(WebhookSubscription.is_active == True)
            
            result = await session.execute(query)
            subscriptions = result.scalars().all()
            
            # Filter by event type if specified
            if event_type:
                subscriptions = [
                    sub for sub in subscriptions
                    if event_type.value in (sub.event_types or [])
                ]
            
            return subscriptions
    
    async def deliver_event(self, event: Event):
        """
        Deliver event to all matching subscriptions
        
        Args:
            event: Event to deliver
        """
        
        # Get matching subscriptions
        subscriptions = await self.get_subscriptions(
            event_type=event.type,
            active_only=True
        )
        
        logger.info(
            f"Delivering event {event.type.value} to "
            f"{len(subscriptions)} subscriptions"
        )
        
        # Queue deliveries
        for subscription in subscriptions:
            await self.delivery_queue.put((event, subscription))
    
    async def _process_delivery(
        self,
        event: Event,
        subscription: WebhookSubscription
    ):
        """
        Process single webhook delivery with retries
        
        Args:
            event: Event to deliver
            subscription: Webhook subscription
        """
        
        max_attempts = subscription.retry_count or self.max_retries
        
        for attempt in range(1, max_attempts + 1):
            try:
                success = await self._attempt_delivery(
                    event=event,
                    subscription=subscription,
                    attempt_number=attempt
                )
                
                if success:
                    logger.info(
                        f"Webhook delivered successfully: {subscription.id} "
                        f"(attempt {attempt})"
                    )
                    return
                
            except Exception as e:
                logger.error(
                    f"Webhook delivery error: {subscription.id} "
                    f"(attempt {attempt}): {e}"
                )
            
            # Wait before retry (exponential backoff)
            if attempt < max_attempts:
                wait_time = 2 ** attempt  # 2, 4, 8 seconds
                await asyncio.sleep(wait_time)
        
        logger.error(
            f"Webhook delivery failed after {max_attempts} attempts: "
            f"{subscription.id}"
        )
    
    async def _attempt_delivery(
        self,
        event: Event,
        subscription: WebhookSubscription,
        attempt_number: int
    ) -> bool:
        """
        Attempt single webhook delivery
        
        Args:
            event: Event to deliver
            subscription: Webhook subscription
            attempt_number: Attempt number
        
        Returns:
            True if successful
        """
        
        delivery_id = f"del_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        
        # Prepare payload
        payload = {
            "id": event.id,
            "type": event.type.value,
            "source": event.source,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        if event.user_id:
            payload["user_id"] = event.user_id
        
        if event.correlation_id:
            payload["correlation_id"] = event.correlation_id
        
        # Generate signature
        signature = self._generate_signature(
            payload=payload,
            secret=subscription.secret
        )
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Id": delivery_id,
            "X-Event-Type": event.type.value,
            "User-Agent": "IOS-Webhook/1.0"
        }
        
        # Make request
        try:
            async with httpx.AsyncClient(timeout=subscription.timeout_seconds) as client:
                response = await client.post(
                    subscription.url,
                    json=payload,
                    headers=headers
                )
                
                response_time = int((time.time() - start_time) * 1000)
                success = 200 <= response.status_code < 300
                
                # Record delivery
                await self._record_delivery(
                    delivery_id=delivery_id,
                    subscription_id=subscription.id,
                    event=event,
                    request_payload=payload,
                    request_headers=headers,
                    response_status=response.status_code,
                    response_body=response.text[:5000],  # Limit size
                    response_time_ms=response_time,
                    success=success,
                    attempt_number=attempt_number
                )
                
                # Update subscription stats
                await self._update_subscription_stats(
                    subscription_id=subscription.id,
                    success=success,
                    error=None if success else f"HTTP {response.status_code}"
                )
                
                return success
                
        except Exception as e:
            response_time = int((time.time() - start_time) * 1000)
            
            # Record failed delivery
            await self._record_delivery(
                delivery_id=delivery_id,
                subscription_id=subscription.id,
                event=event,
                request_payload=payload,
                request_headers=headers,
                response_status=0,
                response_body=None,
                response_time_ms=response_time,
                success=False,
                error_message=str(e),
                attempt_number=attempt_number
            )
            
            # Update subscription stats
            await self._update_subscription_stats(
                subscription_id=subscription.id,
                success=False,
                error=str(e)
            )
            
            return False
    
    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """
        Generate HMAC signature for webhook
        
        Args:
            payload: Request payload
            secret: Webhook secret
        
        Returns:
            Hex signature
        """
        
        import json
        
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def _record_delivery(
        self,
        delivery_id: str,
        subscription_id: str,
        event: Event,
        request_payload: Dict,
        request_headers: Dict,
        response_status: int,
        response_body: Optional[str],
        response_time_ms: int,
        success: bool,
        attempt_number: int,
        error_message: Optional[str] = None
    ):
        """Record webhook delivery attempt"""
        
        async with async_session() as session:
            delivery = WebhookDelivery(
                id=delivery_id,
                subscription_id=subscription_id,
                event_id=event.id,
                event_type=event.type.value,
                request_url=request_payload.get("url"),
                request_payload=request_payload,
                request_headers=request_headers,
                response_status=response_status,
                response_body=response_body,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                attempt_number=attempt_number,
                delivered_at=datetime.utcnow() if success else None
            )
            
            session.add(delivery)
            await session.commit()
    
    async def _update_subscription_stats(
        self,
        subscription_id: str,
        success: bool,
        error: Optional[str]
    ):
        """Update subscription statistics"""
        
        async with async_session() as session:
            result = await session.execute(
                select(WebhookSubscription).where(
                    WebhookSubscription.id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return
            
            subscription.total_deliveries += 1
            
            if success:
                subscription.successful_deliveries += 1
            else:
                subscription.failed_deliveries += 1
                subscription.last_error = error
            
            subscription.last_delivery_at = datetime.utcnow()
            
            await session.commit()
    
    async def start(self):
        """Start webhook delivery worker"""
        
        if self.is_running:
            logger.warning("Webhook manager already running")
            return
        
        self.is_running = True
        logger.info("Webhook manager started")
        
        # Process deliveries from queue
        while self.is_running:
            try:
                # Wait for delivery with timeout
                event, subscription = await asyncio.wait_for(
                    self.delivery_queue.get(),
                    timeout=1.0
                )
                
                await self._process_delivery(event, subscription)
                
            except asyncio.TimeoutError:
                # No deliveries, continue
                continue
            
            except Exception as e:
                logger.error(
                    f"Error processing webhook delivery: {e}",
                    exc_info=True
                )
    
    def stop(self):
        """Stop webhook delivery worker"""
        
        self.is_running = False
        logger.info("Webhook manager stopped")
    
    async def get_delivery_history(
        self,
        subscription_id: str,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """
        Get delivery history for subscription
        
        Args:
            subscription_id: Subscription ID
            limit: Max deliveries to return
        
        Returns:
            List of deliveries
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(WebhookDelivery)
                .where(WebhookDelivery.subscription_id == subscription_id)
                .order_by(WebhookDelivery.created_at.desc())
                .limit(limit)
            )
            
            return result.scalars().all()


# Global webhook manager
webhook_manager = WebhookManager()