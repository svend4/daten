"""
Integration Examples
"""

import asyncio
from ios_core.integrations.slack import slack_integration
from ios_core.integrations.email import email_integration
from ios_core.events.event_bus import event_bus
from ios_core.events.models import Event, EventType


async def slack_example():
    """Slack integration example"""
    
    print("=== Slack Integration ===")
    
    # Simple message
    await slack_integration.send_message(
        text="Hello from IOS System!",
        channel="#general"
    )
    
    # Document notification
    await slack_integration.send_document_notification(
        document_title="Important Report",
        document_id="doc_123",
        action="created",
        user="John Doe"
    )
    
    # Search alert
    await slack_integration.send_search_alert(
        query="nonexistent query",
        results_count=0
    )
    
    # Error notification
    await slack_integration.send_error_notification(
        error_type="Database Error",
        error_message="Connection timeout",
        severity="critical"
    )
    
    print("Slack messages sent!")


async def email_example():
    """Email integration example"""
    
    print("\n=== Email Integration ===")
    
    # Welcome email
    await email_integration.send_welcome_email(
        user_email="user@example.com",
        username="John Doe"
    )
    
    # Document notification
    await email_integration.send_document_notification(
        user_email="user@example.com",
        document_title="Report Q4",
        document_id="doc_456",
        action="updated"
    )
    
    # Password reset
    await email_integration.send_password_reset(
        user_email="user@example.com",
        reset_token="abc123xyz"
    )
    
    print("Emails sent!")


async def event_bus_example():
    """Event bus integration example"""
    
    print("\n=== Event Bus Integration ===")
    
    # Subscribe to events
    @event_bus.subscribe(EventType.DOCUMENT_CREATED)
    async def on_document_created(event: Event):
        print(f"Document created: {event.data.get('id')}")
        
        # Send Slack notification
        await slack_integration.send_document_notification(
            document_title=event.data.get("title", "Untitled"),
            document_id=event.data.get("id"),
            action="created",
            user=event.user_id or "Unknown"
        )
    
    # Publish event
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="example",
        user_id="user_123",
        data={
            "id": "doc_789",
            "title": "Example Document"
        }
    )
    
    await event_bus.publish(event, wait=True)
    
    print("Event published and handled!")


async def webhook_example():
    """Webhook integration example"""
    
    from ios_core.events.webhook_manager import webhook_manager
    
    print("\n=== Webhook Integration ===")
    
    # Create webhook subscription
    subscription = await webhook_manager.create_subscription(
        user_id="user_123",
        name="Example Webhook",
        url="https://webhook.site/unique-url",
        event_types=[
            EventType.DOCUMENT_CREATED,
            EventType.DOCUMENT_UPDATED
        ]
    )
    
    print(f"Created webhook: {subscription.id}")
    
    # Publish event (will trigger webhook)
    event = Event(
        type=EventType.DOCUMENT_CREATED,
        source="example",
        user_id="user_123",
        data={"id": "doc_999", "title": "Test"}
    )
    
    await webhook_manager.deliver_event(event)
    
    print("Webhook delivery queued!")
    
    # Clean up
    await webhook_manager.delete_subscription(subscription.id)


async def main():
    """Run all examples"""
    
    # Note: Configure environment variables first!
    # SLACK_WEBHOOK_URL, SMTP_HOST, etc.
    
    await slack_example()
    await email_example()
    await event_bus_example()
    await webhook_example()


if __name__ == "__main__":
    asyncio.run(main())