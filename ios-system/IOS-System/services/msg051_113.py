#!/usr/bin/env python3
"""
Index all documents for semantic search
"""

import asyncio
import logging
from sqlalchemy import select

from ios_core.database import async_session
from ios_core.models import DocumentModel
from ios_core.ml.embeddings import embedding_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def index_all_documents():
    """Index all documents"""
    
    logger.info("Starting document indexing...")
    
    # Initialize embedding service
    await embedding_service.initialize()
    logger.info("✓ Embedding service initialized")
    
    # Get all documents
    async with async_session() as session:
        result = await session.execute(select(DocumentModel))
        documents = result.scalars().all()
        
        logger.info(f"Found {len(documents)} documents to index")
        
        # Prepare batch
        batch = []
        for doc in documents:
            text = f"{doc.title}\n\n{doc.content}"
            
            batch.append({
                "id": doc.id,
                "text": text,
                "metadata": {
                    "domain_id": doc.domain_id,
                    "domain_name": doc.domain_name,
                    "title": doc.title,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat()
                }
            })
        
        # Index in batches
        batch_size = 32
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(batch), batch_size):
            batch_chunk = batch[i:i + batch_size]
            
            logger.info(f"Indexing batch {i//batch_size + 1}/{(len(batch) + batch_size - 1)//batch_size}")
            
            stats = await embedding_service.index_batch(batch_chunk)
            total_success += stats["success"]
            total_failed += stats["failed"]
            
            # Update database
            for doc in documents[i:i + batch_size]:
                doc.embedding_indexed = True
                from datetime import datetime
                doc.embedding_updated_at = datetime.utcnow()
            
            await session.commit()
        
        logger.info(
            f"✓ Indexing complete: "
            f"{total_success} success, {total_failed} failed"
        )


async def test_search():
    """Test semantic search"""
    
    logger.info("\nTesting semantic search...")
    
    test_queries = [
        "Persönliches Budget",
        "Widerspruch gegen Bescheid",
        "Antrag auf Eingliederungshilfe"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        
        results = await embedding_service.search_similar(
            query=query,
            limit=3,
            score_threshold=0.5
        )
        
        for i, result in enumerate(results, 1):
            logger.info(
                f"  {i}. {result['metadata'].get('title', 'Untitled')} "
                f"(score: {result['score']:.3f})"
            )


if __name__ == "__main__":
    asyncio.run(index_all_documents())
    asyncio.run(test_search())