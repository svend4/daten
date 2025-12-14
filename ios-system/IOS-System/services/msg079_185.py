"""
SDK Usage Examples
"""

import asyncio
from ios_sdk import IOSClient


async def main():
    # Initialize client
    client = IOSClient(api_key="sk_test_...")
    
    print("=== Documents ===")
    
    # Create document
    doc = client.documents.create(
        title="Example Document",
        content="This is an example document created via SDK."
    )
    print(f"Created: {doc.id}")
    
    # List documents
    docs = client.documents.list(limit=10)
    print(f"Found {len(docs)} documents")
    
    # Update document
    doc = client.documents.update(
        doc.id,
        title="Updated Title"
    )
    print(f"Updated: {doc.title}")
    
    print("\n=== Search ===")
    
    # Basic search
    results = client.search.query("personal budget")
    print(f"Basic search: {len(results)} results")
    
    for result in results[:3]:
        print(f"  - {result.title} (score: {result.score})")
    
    # Neural search
    results = client.search.neural(
        query="Persönliches Budget",
        limit=5
    )
    print(f"Neural search: {len(results)} results")
    
    # Semantic search
    results = client.search.semantic(
        query="support for disabled people",
        threshold=0.8
    )
    print(f"Semantic search: {len(results)} results")
    
    print("\n=== Webhooks ===")
    
    # Create webhook
    webhook = client.webhooks.create(
        name="Example Webhook",
        url="https://example.com/webhook",
        event_types=["document.created", "document.updated"]
    )
    print(f"Created webhook: {webhook.id}")
    
    # List webhooks
    webhooks = client.webhooks.list()
    print(f"Found {len(webhooks)} webhooks")
    
    # Delete webhook
    client.webhooks.delete(webhook.id)
    print("Deleted webhook")
    
    # Clean up
    client.documents.delete(doc.id)
    print("\nCleaned up test document")


if __name__ == "__main__":
    asyncio.run(main())