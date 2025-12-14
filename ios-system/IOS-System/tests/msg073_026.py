"""
Tests for webhook manager
"""

import pytest
from unittest.mock import Mock, patch
from ios_core.events.webhook_manager import webhook_manager
from ios_core.events.models import Event, EventType


@pytest.mark.asyncio
async def test_create_subscription():
    """Test creating webhook subscription"""
    
    subscription = await webhook_manager.create_subscription(
        user_id="user123",
        name="Test Webhook",
        url="https://example.com/webhook",
        event_types=[EventType.DOCUMENT_CREATED]
    )
    
    assert subscription.id is not None
    assert subscription.name == "Test Webhook"
    assert subscription.url == "https://example.com/webhook"
    assert subscription.is_active is True
    
    # Cleanup
    await webhook_manager.delete_subscription(subscription.id)


@pytest.mark.asyncio
async def test_get_subscriptions():
    """Test getting subscriptions"""
    
    # Create subscription
    sub = await webhook_manager.create_subscription(
        user_id="user123",
        name="Test",
        url="https://example.com/webhook",
        event_types=[EventType.DOCUMENT_CREATED]
    )
    
    # Get subscriptions
    subscriptions = await webhook_manager.get_subscriptions(
        user_id="user123"
    )
    
    assert len(subscriptions) > 0
    assert any(s.id == sub.id for s in subscriptions)
    
    # Cleanup
    await webhook_manager.delete_subscription(sub.id)


@pytest.mark.asyncio
async def test_update_subscription():
    """Test updating subscription"""
    
    # Create
    sub = await webhook_manager.create_subscription(
        user_id="user123",
        name="Original",
        url="https://example.com/webhook",
        event_types=[EventType.DOCUMENT_CREATED]
    )
    
    # Update
    updated = await webhook_manager.update_subscription(
        sub.id,
        name="Updated",
        is_active=False
    )
    
    assert updated.name == "Updated"
    assert updated.is_active is False
    
    # Cleanup
    await webhook_manager.delete_subscription(sub.id)


@pytest.mark.asyncio
async def test_signature_generation():
    """Test HMAC signature generation"""
    
    payload = {"test": "data"}
    secret = "test_secret"
    
    sig1 = webhook_manager._generate_signature(payload, secret)
    sig2 = webhook_manager._generate_signature(payload, secret)
    
    # Same payload + secret = same signature
    assert sig1 == sig2
    
    # Different secret = different signature
    sig3 = webhook_manager._generate_signature(payload, "different")
    assert sig1 != sig3


@pytest.mark.asyncio
@patch('httpx.AsyncClient.post')
async def test_webhook_delivery(mock_post):
    """Test webhook delivery"""
    
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "OK"
    mock_post.return_value = mock_response
    
    # Create subscription
    sub = await webhook_manager.create_subscription(
        user_id="user123",
        name="Test",
        url="https://example.com/webhook",
        event_types=[EventType.DOCUMENT_CREATED]
    )
    
    # Create event
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="test",
        data={"id": "doc123"}
    )
    
    # Attempt delivery
    success = await webhook_manager._attempt_delivery(
        event=event,
        subscription=sub,
        attempt_number=1
    )
    
    assert success is True
    assert mock_post.called
    
    # Cleanup
    await webhook_manager.delete_subscription(sub.id)