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