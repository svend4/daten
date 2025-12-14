"""
Event Bus - Internal event distribution
"""

import logging
from typing import Callable, Dict, List, Set, Optional, Any
import asyncio
from datetime import datetime
from collections import defaultdict

from .models import Event, EventType

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-memory event bus for internal event distribution
    
    Features:
    - Pub/Sub pattern
    - Async handlers
    - Event filtering
    - Error handling
    - Handler priorities
    
    Usage:
        bus = EventBus()
        
        # Subscribe
        @bus.subscribe(EventType.DOCUMENT_CREATED)
        async def on_document_created(event: Event):
            print(f"Document created: {event.data['id']}")
        
        # Publish
        await bus.publish(Event(
            type=EventType.DOCUMENT_CREATED,
            source="api",
            data={"id": "doc123"}
        ))
    """
    
    def __init__(self):
        # Handlers: EventType -> List[(priority, handler)]
        self.handlers: Dict[EventType, List[tuple[int, Callable]]] = defaultdict(list)
        
        # Wildcard handlers (receive all events)
        self.wildcard_handlers: List[tuple[int, Callable]] = []
        
        # Statistics
        self.published_count = 0
        self.delivered_count = 0
        self.error_count = 0
        
        # Queue for async processing
        self.event_queue = asyncio.Queue()
        self.is_running = False
    
    def subscribe(
        self,
        event_type: Optional[EventType] = None,
        priority: int = 0
    ):
        """
        Decorator to subscribe to events
        
        Args:
            event_type: Event type to listen for (None for all events)
            priority: Handler priority (higher = earlier execution)
        """
        
        def decorator(handler: Callable):
            if event_type is None:
                # Wildcard subscription
                self.wildcard_handlers.append((priority, handler))
                self.wildcard_handlers.sort(key=lambda x: x[0], reverse=True)
            else:
                # Specific event type
                self.handlers[event_type].append((priority, handler))
                self.handlers[event_type].sort(key=lambda x: x[0], reverse=True)
            
            logger.info(
                f"Subscribed {handler.__name__} to "
                f"{event_type.value if event_type else '*'} "
                f"(priority={priority})"
            )
            
            return handler
        
        return decorator
    
    async def publish(
        self,
        event: Event,
        wait: bool = False
    ):
        """
        Publish event to bus
        
        Args:
            event: Event to publish
            wait: If True, wait for handlers to complete
        """
        
        self.published_count += 1
        
        if not event.id:
            event.id = f"evt_{datetime.utcnow().timestamp()}"
        
        logger.debug(f"Publishing event: {event.type.value} (id={event.id})")
        
        if wait:
            # Synchronous delivery
            await self._deliver_event(event)
        else:
            # Async delivery via queue
            await self.event_queue.put(event)
    
    async def _deliver_event(self, event: Event):
        """Deliver event to all subscribed handlers"""
        
        # Get handlers for this event type
        type_handlers = self.handlers.get(event.type, [])
        
        # Combine with wildcard handlers
        all_handlers = type_handlers + self.wildcard_handlers
        
        # Sort by priority
        all_handlers.sort(key=lambda x: x[0], reverse=True)
        
        # Execute handlers
        for priority, handler in all_handlers:
            try:
                await handler(event)
                self.delivered_count += 1
                
                logger.debug(
                    f"Delivered {event.type.value} to {handler.__name__}"
                )
                
            except Exception as e:
                self.error_count += 1
                logger.error(
                    f"Error in handler {handler.__name__} "
                    f"for event {event.type.value}: {e}",
                    exc_info=True
                )
    
    async def start(self):
        """Start event processing loop"""
        
        if self.is_running:
            logger.warning("Event bus already running")
            return
        
        self.is_running = True
        logger.info("Event bus started")
        
        # Process events from queue
        while self.is_running:
            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                await self._deliver_event(event)
                
            except asyncio.TimeoutError:
                # No events, continue
                continue
            
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)
    
    def stop(self):
        """Stop event processing loop"""
        
        self.is_running = False
        logger.info("Event bus stopped")
    
    def get_stats(self) -> Dict:
        """Get event bus statistics"""
        
        total_handlers = sum(len(h) for h in self.handlers.values())
        total_handlers += len(self.wildcard_handlers)
        
        return {
            "published": self.published_count,
            "delivered": self.delivered_count,
            "errors": self.error_count,
            "total_handlers": total_handlers,
            "event_types": len(self.handlers),
            "queue_size": self.event_queue.qsize(),
            "is_running": self.is_running
        }


# Global event bus
event_bus = EventBus()