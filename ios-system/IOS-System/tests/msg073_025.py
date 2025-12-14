"""
Tests for event bus
"""

import pytest
import asyncio
from ios_core.events.event_bus import EventBus
from ios_core.events.models import Event, EventType


@pytest.fixture
def bus():
    """Create event bus"""
    return EventBus()


@pytest.mark.asyncio
async def test_subscribe_and_publish(bus):
    """Test basic pub/sub"""
    
    received_events = []
    
    @bus.subscribe(EventType.DOCUMENT_CREATED)
    async def handler(event: Event):
        received_events.append(event)
    
    # Publish event
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={"id": "doc123"}
    )
    
    await bus.publish(event, wait=True)
    
    assert len(received_events) == 1
    assert received_events[0].data["id"] == "doc123"


@pytest.mark.asyncio
async def test_wildcard_subscription(bus):
    """Test wildcard subscription"""
    
    received_events = []
    
    @bus.subscribe()  # No event type = wildcard
    async def handler(event: Event):
        received_events.append(event)
    
    # Publish different event types
    await bus.publish(
        Event(type=EventType.DOCUMENT_CREATED, source="test", data={}),
        wait=True
    )
    
    await bus.publish(
        Event(type=EventType.USER_LOGIN, source="test", data={}),
        wait=True
    )
    
    assert len(received_events) == 2


@pytest.mark.asyncio
async def test_handler_priority(bus):
    """Test handler priorities"""
    
    execution_order = []
    
    @bus.subscribe(EventType.DOCUMENT_CREATED, priority=1)
    async def low_priority(event: Event):
        execution_order.append("low")
    
    @bus.subscribe(EventType.DOCUMENT_CREATED, priority=10)
    async def high_priority(event: Event):
        execution_order.append("high")
    
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={}
    )
    
    await bus.publish(event, wait=True)
    
    # High priority should execute first
    assert execution_order == ["high", "low"]


@pytest.mark.asyncio
async def test_error_handling(bus):
    """Test handler error handling"""
    
    received_events = []
    
    @bus.subscribe(EventType.DOCUMENT_CREATED)
    async def failing_handler(event: Event):
        raise Exception("Handler error")
    
    @bus.subscribe(EventType.DOCUMENT_CREATED)
    async def working_handler(event: Event):
        received_events.append(event)
    
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={}
    )
    
    # Should not raise, should continue to other handlers
    await bus.publish(event, wait=True)
    
    assert len(received_events) == 1


@pytest.mark.asyncio
async def test_async_queue(bus):
    """Test async event queue"""
    
    received_events = []
    
    @bus.subscribe(EventType.DOCUMENT_CREATED)
    async def handler(event: Event):
        received_events.append(event)
    
    # Start event bus
    bus_task = asyncio.create_task(bus.start())
    
    # Publish event (async)
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={"id": "doc123"}
    )
    
    await bus.publish(event, wait=False)
    
    # Wait for processing
    await asyncio.sleep(0.1)
    
    # Stop bus
    bus.stop()
    await bus_task
    
    assert len(received_events) == 1


@pytest.mark.asyncio
async def test_get_stats(bus):
    """Test statistics"""
    
    @bus.subscribe(EventType.DOCUMENT_CREATED)
    async def handler(event: Event):
        pass
    
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={}
    )
    
    await bus.publish(event, wait=True)
    
    stats = bus.get_stats()
    
    assert stats["published"] >= 1
    assert stats["delivered"] >= 1
    assert stats["total_handlers"] >= 1