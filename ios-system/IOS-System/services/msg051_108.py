"""
Background tasks for embedding generation
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio

from ..database import async_session
from ..models import DocumentModel
from ..ml.embeddings import embedding_service
from ..ml.bert_client import bert_client
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)


class EmbeddingTaskManager:
    """
    Manage background embedding tasks
    
    Features:
    - Index new documents automatically
    - Re-index updated documents
    - Batch processing for efficiency
    - Error handling and retry logic
    """
    
    def __init__(self):
        self.running = False
        self.batch_size = 32
        self.check_interval = 60  # seconds
    
    async def start(self):
        """Start background task runner"""
        
        self.running = True
        logger.info("Embedding task manager started")
        
        # Initialize embedding service
        await embedding_service.initialize()
        
        # Start task loop
        while self.running:
            try:
                await self._process_pending_documents()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in embedding task loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    def stop(self):
        """Stop background tasks"""
        self.running = False
        logger.info("Embedding task manager stopped")
    
    async def _process_pending_documents(self):
        """Process documents that need embedding"""
        
        async with async_session() as session:
            # Find documents without embeddings or with stale embeddings
            stmt = select(DocumentModel).where(
                or_(
                    DocumentModel.embedding_indexed == False,
                    DocumentModel.embedding_indexed == None,
                    and_(
                        DocumentModel.updated_at > DocumentModel.embedding_updated_at,
                        DocumentModel.embedding_updated_at != None
                    )
                )
            ).limit(self.batch_size)
            
            result = await session.execute(stmt)
            documents = result.scalars().all()
            
            if not documents:
                logger.debug("No pending documents to index")
                return
            
            logger.info(f"Processing {len(documents)} documents for embedding")
            
            # Prepare batch
            batch = []
            for doc in documents:
                # Combine title and content
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
            
            # Index batch
            stats = await embedding_service.index_batch(batch)
            
            # Update database
            for doc in documents:
                doc.embedding_indexed = True
                doc.embedding_updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(
                f"Batch indexing complete: "
                f"{stats['success']} success, {stats['failed']} failed"
            )
    
    async def index_document(
        self,
        doc_id: str,
        priority: bool = False
    ) -> bool:
        """
        Index single document
        
        Args:
            doc_id: Document ID
            priority: If True, index immediately (don't wait for batch)
        
        Returns:
            Success status
        """
        
        async with async_session() as session:
            # Get document
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                logger.error(f"Document not found: {doc_id}")
                return False
            
            # Prepare text
            text = f"{doc.title}\n\n{doc.content}"
            
            # Index
            success = await embedding_service.index_document(
                doc_id=doc.id,
                text=text,
                metadata={
                    "domain_id": doc.domain_id,
                    "domain_name": doc.domain_name,
                    "title": doc.title,
                    "created_at": doc.created_at.isoformat(),
                    "updated_at": doc.updated_at.isoformat()
                }
            )
            
            if success:
                # Update database
                doc.embedding_indexed = True
                doc.embedding_updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"Indexed document: {doc_id}")
            
            return success
    
    async def reindex_domain(
        self,
        domain_id: str
    ) -> Dict[str, int]:
        """
        Re-index all documents in a domain
        
        Args:
            domain_id: Domain ID
        
        Returns:
            Statistics (success, failed)
        """
        
        logger.info(f"Re-indexing domain: {domain_id}")
        
        async with async_session() as session:
            # Get all documents in domain
            stmt = select(DocumentModel).where(
                DocumentModel.domain_id == domain_id
            )
            result = await session.execute(stmt)
            documents = result.scalars().all()
            
            logger.info(f"Found {len(documents)} documents in domain")
            
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
            
            # Index batch
            stats = await embedding_service.index_batch(batch)
            
            # Update database
            for doc in documents:
                doc.embedding_indexed = True
                doc.embedding_updated_at = datetime.utcnow()
            
            await session.commit()
            
            logger.info(f"Domain re-indexing complete: {stats}")
            return stats
    
    async def delete_document_embedding(
        self,
        doc_id: str
    ) -> bool:
        """Delete document from embedding index"""
        
        success = await embedding_service.delete_document(doc_id)
        
        if success:
            async with async_session() as session:
                result = await session.execute(
                    select(DocumentModel).where(DocumentModel.id == doc_id)
                )
                doc = result.scalar_one_or_none()
                
                if doc:
                    doc.embedding_indexed = False
                    doc.embedding_updated_at = None
                    await session.commit()
        
        return success


# Global task manager
embedding_task_manager = EmbeddingTaskManager()