"""
Event Store - Persistent event storage
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import uuid

from .models import Event, EventType
from ..database import async_session
from sqlalchemy import Column, String, DateTime, JSON, select, and_

logger = logging.getLogger(__name__)


class StoredEvent:
    """Database model for stored events"""
    
    from ..database import Base
    
    class Model(Base):
        __tablename__ = "stored_events"
        
        id = Column(String(50), primary_key=True)
        type = Column(String(100), nullable=False, index=True)
        source = Column(String(200), nullable=False)
        user_id = Column(String(50), index=True)
        correlation_id = Column(String(50), index=True)
        data = Column(JSON, nullable=False)
        timestamp = Column(DateTime, nullable=False, index=True)
        created_at = Column(DateTime, default=datetime.utcnow)


class EventStore:
    """
    Persistent event storage
    
    Features:
    - Event persistence
    - Event replay
    - Query by type/user/time
    - Event sourcing support
    - Automatic cleanup
    
    Usage:
        store = EventStore()
        
        # Store event
        await store.store(event)
        
        # Query events
        events = await store.get_events(
            event_type=EventType.DOCUMENT_CREATED,
            user_id="user123"
        )
    """
    
    def __init__(self, retention_days: int = 90):
        self.retention_days = retention_days
    
    async def store(self, event: Event):
        """
        Store event in database
        
        Args:
            event: Event to store
        """
        
        async with async_session() as session:
            if not event.id:
                event.id = f"evt_{uuid.uuid4().hex[:12]}"
            
            stored_event = StoredEvent.Model(
                id=event.id,
                type=event.type.value,
                source=event.source,
                user_id=event.user_id,
                correlation_id=event.correlation_id,
                data=event.data,
                timestamp=event.timestamp
            )
            
            session.add(stored_event)
            await session.commit()
            
            logger.debug(f"Stored event: {event.id} ({event.type.value})")
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        """
        Get event by ID
        
        Args:
            event_id: Event ID
        
        Returns:
            Event or None
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(StoredEvent.Model).where(
                    StoredEvent.Model.id == event_id
                )
            )
            stored = result.scalar_one_or_none()
            
            if not stored:
                return None
            
            return self._to_event(stored)
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Query events
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user
            correlation_id: Filter by correlation ID
            start_time: Events after this time
            end_time: Events before this time
            limit: Max events to return
        
        Returns:
            List of events
        """
        
        async with async_session() as session:
            query = select(StoredEvent.Model)
            
            # Build filters
            filters = []
            
            if event_type:
                filters.append(StoredEvent.Model.type == event_type.value)
            
            if user_id:
                filters.append(StoredEvent.Model.user_id == user_id)
            
            if correlation_id:
                filters.append(StoredEvent.Model.correlation_id == correlation_id)
            
            if start_time:
                filters.append(StoredEvent.Model.timestamp >= start_time)
            
            if end_time:
                filters.append(StoredEvent.Model.timestamp <= end_time)
            
            if filters:
                query = query.where(and_(*filters))
            
            # Order and limit
            query = query.order_by(
                StoredEvent.Model.timestamp.desc()
            ).limit(limit)
            
            result = await session.execute(query)
            stored_events = result.scalars().all()
            
            return [self._to_event(se) for se in stored_events]
    
    async def get_event_stream(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get event stream for replay/audit
        
        Args:
            start_time: Start of stream
            end_time: End of stream (None = now)
        
        Returns:
            Events in chronological order
        """
        
        if not end_time:
            end_time = datetime.utcnow()
        
        events = await self.get_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000  # High limit for replay
        )
        
        # Reverse to chronological order
        return list(reversed(events))
    
    async def cleanup_old_events(self, days: Optional[int] = None):
        """
        Delete old events
        
        Args:
            days: Delete events older than this (default: retention_days)
        """
        
        days = days or self.retention_days
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        async with async_session() as session:
            result = await session.execute(
                select(StoredEvent.Model).where(
                    StoredEvent.Model.timestamp < cutoff
                )
            )
            
            old_events = result.scalars().all()
            
            for event in old_events:
                await session.delete(event)
            
            await session.commit()
            
            logger.info(
                f"Cleaned up {len(old_events)} events older than {days} days"
            )
    
    async def get_stats(self) -> Dict:
        """Get event store statistics"""
        
        async with async_session() as session:
            # Total events
            result = await session.execute(
                select(func.count(StoredEvent.Model.id))
            )
            total = result.scalar()
            
            # Events by type
            result = await session.execute(
                select(
                    StoredEvent.Model.type,
                    func.count(StoredEvent.Model.id)
                ).group_by(StoredEvent.Model.type)
            )
            by_type = dict(result.all())
            
            # Events in last 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            result = await session.execute(
                select(func.count(StoredEvent.Model.id)).where(
                    StoredEvent.Model.timestamp >= yesterday
                )
            )
            last_24h = result.scalar()
            
            return {
                "total_events": total,
                "events_24h": last_24h,
                "events_by_type": by_type,
                "retention_days": self.retention_days
            }
    
    def _to_event(self, stored: StoredEvent.Model) -> Event:
        """Convert stored event to Event model"""
        
        return Event(
            id=stored.id,
            type=EventType(stored.type),
            source=stored.source,
            data=stored.data,
            timestamp=stored.timestamp,
            user_id=stored.user_id,
            correlation_id=stored.correlation_id
        )


# Global event store
event_store = EventStore()