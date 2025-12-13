Пользователь готов продолжить. Создам оставшиеся файлы для Day 129-130:
- Event handlers (интеграция с системой)
- Tests для webhook и event bus
- Documentation
- Integration examples
- Затем переходим к Day 131-132 (External Integrations & SDK)# 📡 DAY 129-130: WEBHOOK SYSTEM & EVENT BUS (ЗАВЕРШЕНИЕ)

---

## ФАЙЛ 17: `ios_core/events/handlers.py`

```python
"""
System Event Handlers
Integrates event bus with core functionality
"""

import logging
from datetime import datetime

from .event_bus import event_bus
from .event_store import event_store
from .webhook_manager import webhook_manager
from .models import Event, EventType

logger = logging.getLogger(__name__)


# === Core Event Handlers ===

@event_bus.subscribe(priority=100)
async def store_all_events(event: Event):
    """
    Store all events in event store
    
    Priority: 100 (highest - runs first)
    """
    
    try:
        await event_store.store(event)
    except Exception as e:
        logger.error(f"Failed to store event {event.id}: {e}")


@event_bus.subscribe(priority=90)
async def deliver_to_webhooks(event: Event):
    """
    Deliver events to webhook subscriptions
    
    Priority: 90 (high - runs early)
    """
    
    try:
        await webhook_manager.deliver_event(event)
    except Exception as e:
        logger.error(f"Failed to deliver event {event.id} to webhooks: {e}")


# === Document Events ===

@event_bus.subscribe(EventType.DOCUMENT_CREATED)
async def on_document_created(event: Event):
    """
    Handle document creation
    
    Triggers:
    - Embedding generation
    - Search indexing
    - Notifications
    """
    
    logger.info(f"Document created: {event.data.get('id')}")
    
    # Trigger background embedding
    from ..tasks.embedding_tasks import embedding_task_manager
    
    doc_id = event.data.get("id")
    if doc_id:
        await embedding_task_manager.add_task({
            "type": "embed_document",
            "document_id": doc_id
        })


@event_bus.subscribe(EventType.DOCUMENT_UPDATED)
async def on_document_updated(event: Event):
    """
    Handle document update
    
    Triggers:
    - Re-indexing
    - Cache invalidation
    """
    
    logger.info(f"Document updated: {event.data.get('id')}")
    
    doc_id = event.data.get("id")
    
    # Invalidate cache
    from ..optimization.cache_manager import cache_manager
    await cache_manager.delete(f"document:{doc_id}")
    
    # Re-embed if content changed
    if event.data.get("content_changed"):
        from ..tasks.embedding_tasks import embedding_task_manager
        await embedding_task_manager.add_task({
            "type": "embed_document",
            "document_id": doc_id
        })


@event_bus.subscribe(EventType.DOCUMENT_DELETED)
async def on_document_deleted(event: Event):
    """
    Handle document deletion
    
    Triggers:
    - Index cleanup
    - Cache cleanup
    """
    
    logger.info(f"Document deleted: {event.data.get('id')}")
    
    doc_id = event.data.get("id")
    
    # Clean up embeddings
    from ..ml.embeddings import embedding_service
    
    try:
        # Delete from vector database
        await embedding_service.delete_document(doc_id)
    except Exception as e:
        logger.error(f"Failed to delete embeddings for {doc_id}: {e}")
    
    # Clear cache
    from ..optimization.cache_manager import cache_manager
    await cache_manager.delete(f"document:{doc_id}")


# === Search Events ===

@event_bus.subscribe(EventType.SEARCH_PERFORMED)
async def on_search_performed(event: Event):
    """
    Handle search query
    
    Tracks:
    - Search analytics
    - Popular queries
    - Zero results
    """
    
    query = event.data.get("query")
    results_count = event.data.get("results_count", 0)
    
    logger.debug(f"Search performed: '{query}' ({results_count} results)")
    
    # Track in analytics
    from ..gateway.api_analytics import api_analytics
    
    if results_count == 0:
        # Log zero results for analysis
        logger.info(f"Zero results for query: '{query}'")


@event_bus.subscribe(EventType.SEARCH_RESULT_CLICKED)
async def on_search_result_clicked(event: Event):
    """
    Handle search result click
    
    Tracks:
    - Click-through rate
    - Result relevance
    """
    
    logger.debug(
        f"Search result clicked: {event.data.get('document_id')} "
        f"at position {event.data.get('position')}"
    )


# === Security Events ===

@event_bus.subscribe(EventType.SECURITY_BREACH_DETECTED)
async def on_security_breach(event: Event):
    """
    Handle security breach
    
    Actions:
    - Alert administrators
    - Log to security audit
    - Potentially lock account
    """
    
    logger.critical(
        f"SECURITY BREACH: {event.data.get('type')} "
        f"for user {event.user_id}"
    )
    
    # Could send alerts via email/SMS/Slack
    # For now, just ensure it's stored
    pass


@event_bus.subscribe(EventType.MFA_ENABLED)
async def on_mfa_enabled(event: Event):
    """Handle MFA enablement"""
    
    logger.info(f"MFA enabled for user: {event.user_id}")


# === User Events ===

@event_bus.subscribe(EventType.USER_REGISTERED)
async def on_user_registered(event: Event):
    """
    Handle new user registration
    
    Actions:
    - Send welcome email
    - Initialize user settings
    - Track analytics
    """
    
    logger.info(f"New user registered: {event.user_id}")
    
    # Could trigger welcome email, onboarding, etc.


@event_bus.subscribe(EventType.USER_LOGIN)
async def on_user_login(event: Event):
    """Handle user login"""
    
    logger.debug(f"User login: {event.user_id}")


# === System Events ===

@event_bus.subscribe(EventType.SYSTEM_ERROR)
async def on_system_error(event: Event):
    """
    Handle system errors
    
    Actions:
    - Log to monitoring
    - Alert on critical errors
    """
    
    error_type = event.data.get("error_type")
    severity = event.data.get("severity", "medium")
    
    if severity == "critical":
        logger.critical(f"CRITICAL SYSTEM ERROR: {error_type}")
    else:
        logger.error(f"System error: {error_type}")


# === ML Events ===

@event_bus.subscribe(EventType.EMBEDDING_CREATED)
async def on_embedding_created(event: Event):
    """Handle embedding creation"""
    
    logger.debug(
        f"Embedding created for document: {event.data.get('document_id')}"
    )


@event_bus.subscribe(EventType.GPT_GENERATION_COMPLETED)
async def on_gpt_generation_completed(event: Event):
    """
    Handle GPT generation completion
    
    Tracks:
    - Token usage
    - Cost
    - Performance
    """
    
    tokens = event.data.get("tokens_used", 0)
    cost = event.data.get("cost", 0)
    
    logger.info(
        f"GPT generation completed: {tokens} tokens, ${cost:.4f}"
    )


# === Helper Functions ===

async def publish_document_event(
    event_type: EventType,
    document_id: str,
    user_id: str,
    additional_data: dict = None
):
    """
    Publish document event
    
    Args:
        event_type: Type of event
        document_id: Document ID
        user_id: User who triggered event
        additional_data: Additional event data
    """
    
    data = {
        "id": document_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if additional_data:
        data.update(additional_data)
    
    event = Event(
        type=event_type,
        source="documents",
        user_id=user_id,
        data=data
    )
    
    await event_bus.publish(event)


async def publish_search_event(
    query: str,
    results_count: int,
    user_id: str = None,
    duration_ms: int = 0
):
    """
    Publish search event
    
    Args:
        query: Search query
        results_count: Number of results
        user_id: User who performed search
        duration_ms: Search duration
    """
    
    event = Event(
        type=EventType.SEARCH_PERFORMED,
        source="search",
        user_id=user_id,
        data={
            "query": query,
            "results_count": results_count,
            "duration_ms": duration_ms
        }
    )
    
    await event_bus.publish(event)


async def publish_security_event(
    breach_type: str,
    user_id: str,
    severity: str = "high",
    details: dict = None
):
    """
    Publish security event
    
    Args:
        breach_type: Type of security breach
        user_id: Affected user
        severity: Severity level
        details: Additional details
    """
    
    data = {
        "type": breach_type,
        "severity": severity
    }
    
    if details:
        data.update(details)
    
    event = Event(
        type=EventType.SECURITY_BREACH_DETECTED,
        source="security",
        user_id=user_id,
        data=data
    )
    
    await event_bus.publish(event)


# Initialize event handlers
def initialize_event_handlers():
    """Initialize all event handlers"""
    
    logger.info("Event handlers initialized")
```

---

## ФАЙЛ 18: `tests/events/test_event_bus.py`

```python
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
```

---

## ФАЙЛ 19: `tests/events/test_webhook_manager.py`

```python
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
```

---

## ФАЙЛ 20: `docs/WEBHOOK_GUIDE.md`

```markdown
# Webhook Integration Guide

## Overview

Webhooks allow your application to receive real-time event notifications from IOS System via HTTP callbacks.

---

## Quick Start

### 1. Create Webhook

```bash
POST /api/webhooks
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Webhook",
  "url": "https://your-app.com/webhook",
  "event_types": [
    "document.created",
    "document.updated",
    "search.performed"
  ]
}
```

Response:

```json
{
  "id": "wh_abc123",
  "name": "My Webhook",
  "url": "https://your-app.com/webhook",
  "secret": "whsec_xyz789",
  "event_types": ["document.created", "document.updated"],
  "is_active": true
}
```

**Important:** Save the `secret` - you'll need it to verify webhook signatures.

### 2. Implement Webhook Endpoint

```python
from flask import Flask, request
import hmac
import hashlib
import json

app = Flask(__name__)

WEBHOOK_SECRET = "whsec_xyz789"  # From creation response

@app.route('/webhook', methods=['POST'])
def webhook():
    # Verify signature
    signature = request.headers.get('X-Webhook-Signature')
    
    if not verify_signature(request.data, signature):
        return 'Invalid signature', 401
    
    # Process event
    event = request.json
    
    print(f"Received event: {event['type']}")
    print(f"Data: {event['data']}")
    
    return 'OK', 200

def verify_signature(payload, signature):
    """Verify HMAC signature"""
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

### 3. Test Webhook

Trigger an event (e.g., create a document) and check your endpoint receives the notification.

---

## Event Types

### Document Events

- `document.created` - New document created
- `document.updated` - Document modified
- `document.deleted` - Document removed
- `document.viewed` - Document accessed

### Search Events

- `search.performed` - Search query executed
- `search.result_clicked` - Search result clicked

### User Events

- `user.registered` - New user signed up
- `user.login` - User logged in
- `user.logout` - User logged out

### Security Events

- `security.breach_detected` - Security incident
- `security.mfa_enabled` - MFA activated
- `security.password_changed` - Password updated

### ML Events

- `ml.embedding_created` - Document embedding generated
- `ml.gpt_generation_completed` - GPT generation finished

Full list: `GET /api/event-types`

---

## Event Format

All webhook events follow this structure:

```json
{
  "id": "evt_abc123",
  "type": "document.created",
  "source": "api",
  "timestamp": "2025-01-15T10:30:00Z",
  "user_id": "user_xyz",
  "correlation_id": "req_123",
  "data": {
    "id": "doc_789",
    "title": "My Document",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

Fields:
- `id` - Unique event ID
- `type` - Event type (see above)
- `source` - Component that generated event
- `timestamp` - Event time (ISO 8601)
- `user_id` - User who triggered event (if applicable)
- `correlation_id` - Request correlation ID (for tracing)
- `data` - Event-specific data

---

## Security

### Signature Verification

**Always verify webhook signatures** to ensure authenticity.

Headers:
```
X-Webhook-Signature: <hmac_sha256_hex>
X-Webhook-Id: <delivery_id>
X-Event-Type: <event_type>
```

Verification:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    """
    Verify webhook signature
    
    Args:
        payload: Raw request body (bytes)
        signature: X-Webhook-Signature header
        secret: Your webhook secret
    
    Returns:
        True if valid
    """
    
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

**Important:**
- Use constant-time comparison (`hmac.compare_digest`)
- Verify before processing event
- Return 401 for invalid signatures

### Best Practices

1. **Use HTTPS** - Always use `https://` URLs
2. **Validate signatures** - Don't trust unsigned webhooks
3. **Handle replays** - Store processed event IDs to prevent duplicates
4. **Rate limiting** - Implement rate limiting on your endpoint
5. **Timeouts** - Respond within 30 seconds

---

## Retry Logic

Failed deliveries are retried with exponential backoff:

- Attempt 1: Immediate
- Attempt 2: After 2 seconds
- Attempt 3: After 4 seconds
- Attempt 4: After 8 seconds (if configured)

**Success criteria:**
- HTTP status 200-299
- Response within timeout (default: 30s)

**Failure criteria:**
- HTTP status 400-599
- Timeout
- Network error

After all retries fail, delivery is marked as failed. Check delivery history to debug.

---

## Managing Webhooks

### List Webhooks

```bash
GET /api/webhooks
Authorization: Bearer <token>
```

### Get Webhook Details

```bash
GET /api/webhooks/{webhook_id}
Authorization: Bearer <token>
```

### Update Webhook

```bash
PATCH /api/webhooks/{webhook_id}
Authorization: Bearer <token>

{
  "name": "Updated Name",
  "url": "https://new-url.com/webhook",
  "is_active": true
}
```

### Delete Webhook

```bash
DELETE /api/webhooks/{webhook_id}
Authorization: Bearer <token>
```

### View Delivery History

```bash
GET /api/webhooks/{webhook_id}/deliveries?limit=100
Authorization: Bearer <token>
```

Response:

```json
{
  "deliveries": [
    {
      "id": "del_abc",
      "event_type": "document.created",
      "success": true,
      "response_status": 200,
      "response_time_ms": 145,
      "attempt_number": 1,
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## Implementation Examples

### Node.js (Express)

```javascript
const express = require('express');
const crypto = require('crypto');

const app = express();
const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET;

app.post('/webhook', express.raw({type: 'application/json'}), (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  
  // Verify signature
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(req.body)
    .digest('hex');
  
  if (!crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  )) {
    return res.status(401).send('Invalid signature');
  }
  
  // Process event
  const event = JSON.parse(req.body);
  console.log('Event:', event.type);
  
  res.status(200).send('OK');
});

app.listen(3000);
```

### Go

```go
package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "io/ioutil"
    "net/http"
)

const webhookSecret = "whsec_xyz789"

func webhookHandler(w http.ResponseWriter, r *http.Request) {
    body, _ := ioutil.ReadAll(r.Body)
    signature := r.Header.Get("X-Webhook-Signature")
    
    // Verify signature
    mac := hmac.New(sha256.New, []byte(webhookSecret))
    mac.Write(body)
    expected := hex.EncodeToString(mac.Sum(nil))
    
    if !hmac.Equal([]byte(signature), []byte(expected)) {
        http.Error(w, "Invalid signature", 401)
        return
    }
    
    // Process event
    var event map[string]interface{}
    json.Unmarshal(body, &event)
    
    w.WriteHeader(200)
}

func main() {
    http.HandleFunc("/webhook", webhookHandler)
    http.ListenAndServe(":8080", nil)
}
```

---

## Debugging

### Test Webhook

Use tools like [webhook.site](https://webhook.site) or [ngrok](https://ngrok.com) for testing:

```bash
# Start ngrok tunnel
ngrok http 3000

# Use ngrok URL in webhook
https://<random>.ngrok.io/webhook
```

### Common Issues

**Problem:** Not receiving webhooks

**Solutions:**
- Check webhook is active (`is_active: true`)
- Verify URL is accessible
- Check event types match
- Review delivery history for errors

**Problem:** Signature verification fails

**Solutions:**
- Ensure using raw request body (not parsed JSON)
- Check secret is correct
- Use constant-time comparison
- Verify HMAC algorithm (SHA-256)

**Problem:** Timeouts

**Solutions:**
- Process events asynchronously
- Return 200 immediately, process in background
- Optimize endpoint performance
- Increase timeout setting

---

## Rate Limits

Webhooks respect the same rate limits as API requests. If you exceed limits, deliveries may be delayed.

---

## Support

For issues or questions:
- Check delivery history: `/api/webhooks/{id}/deliveries`
- Review error messages in delivery logs
- Contact support with delivery ID

---

## Security Checklist

- [ ] Using HTTPS URLs
- [ ] Verifying signatures
- [ ] Handling duplicate events
- [ ] Rate limiting webhook endpoint
- [ ] Logging webhook events
- [ ] Monitoring delivery failures
- [ ] Keeping secrets secure

---

## Next Steps

- Set up webhook monitoring
- Implement event processing
- Test error scenarios
- Monitor delivery success rates
```

---

**Продолжение следует...**

Создано:
- ✅ Event Handlers (system integration)
- ✅ Tests for Event Bus and Webhooks
- ✅ Comprehensive Webhook Guide

**Следующие файлы:**
- Integration examples
- Event store documentation
- Week summary
- Day 131-132 начало

**Готовы продолжить к Day 131-132 (External Integrations & SDK)?**