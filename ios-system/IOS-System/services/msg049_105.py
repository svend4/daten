"""
Embedding Service
Manages document embeddings with Qdrant vector database
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import asyncio

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from .bert_client import bert_client
from ..config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Manage document embeddings
    
    Features:
    - Store embeddings in Qdrant
    - Semantic similarity search
    - Batch processing
    - Incremental updates
    
    Usage:
        service = EmbeddingService()
        await service.initialize()
        
        # Index document
        await service.index_document(
            doc_id="doc123",
            text="Document content...",
            metadata={"domain": "SGB-IX"}
        )
        
        # Search similar
        results = await service.search_similar(
            query="Persönliches Budget",
            limit=10
        )
    """
    
    COLLECTION_NAME = "ios_documents"
    EMBEDDING_DIM = 1024  # GBERT-large dimension
    
    def __init__(self):
        self.client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Qdrant client and collection"""
        
        if self.initialized:
            return
        
        try:
            # Connect to Qdrant
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port
            )
            
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.COLLECTION_NAME
                for col in collections
            )
            
            if not collection_exists:
                # Create collection
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {self.COLLECTION_NAME}")
            else:
                logger.info(f"Collection exists: {self.COLLECTION_NAME}")
            
            self.initialized = True
            logger.info("Embedding service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def index_document(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Index a document
        
        Args:
            doc_id: Document ID
            text: Document text
            metadata: Additional metadata
        
        Returns:
            Success status
        """
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get embedding
            embedding = await bert_client.embed_single(text)
            
            # Create point
            point = PointStruct(
                id=doc_id,
                vector=embedding,
                payload={
                    "text": text[:1000],  # Store preview
                    "indexed_at": datetime.utcnow().isoformat(),
                    **(metadata or {})
                }
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[point]
            )
            
            logger.debug(f"Indexed document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False
    
    async def index_batch(
        self,
        documents: List[Dict]
    ) -> Dict[str, int]:
        """
        Index multiple documents
        
        Args:
            documents: List of dicts with 'id', 'text', 'metadata'
        
        Returns:
            Statistics (success, failed)
        """
        
        stats = {"success": 0, "failed": 0}
        
        # Process in batches
        batch_size = 32
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            try:
                # Get embeddings for batch
                texts = [doc["text"] for doc in batch]
                embeddings = await bert_client.embed(texts)
                
                # Create points
                points = []
                for doc, embedding in zip(batch, embeddings):
                    points.append(
                        PointStruct(
                            id=doc["id"],
                            vector=embedding,
                            payload={
                                "text": doc["text"][:1000],
                                "indexed_at": datetime.utcnow().isoformat(),
                                **doc.get("metadata", {})
                            }
                        )
                    )
                
                # Upsert batch
                self.client.upsert(
                    collection_name=self.COLLECTION_NAME,
                    points=points
                )
                
                stats["success"] += len(batch)
                
            except Exception as e:
                logger.error(f"Batch indexing error: {e}")
                stats["failed"] += len(batch)
        
        logger.info(f"Batch indexing complete: {stats}")
        return stats
    
    async def search_similar(
        self,
        query: str,
        limit: int = 10,
        domain_filter: Optional[str] = None,
        score_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            limit: Max results
            domain_filter: Filter by domain
            score_threshold: Minimum similarity score
        
        Returns:
            List of similar documents with scores
        """
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Get query embedding
            query_embedding = await bert_client.embed_single(query)
            
            # Build filter
            query_filter = None
            if domain_filter:
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="domain_name",
                            match=MatchValue(value=domain_filter)
                        )
                    ]
                )
            
            # Search
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "metadata": {
                        k: v for k, v in result.payload.items()
                        if k not in ["text", "indexed_at"]
                    }
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            return []
    
    async def get_similar_to_document(
        self,
        doc_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find documents similar to given document
        
        Args:
            doc_id: Source document ID
            limit: Max results
        
        Returns:
            List of similar documents
        """
        
        try:
            # Get document
            doc = self.client.retrieve(
                collection_name=self.COLLECTION_NAME,
                ids=[doc_id]
            )
            
            if not doc:
                return []
            
            # Get vector
            vector = doc[0].vector
            
            # Search similar (excluding self)
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=vector,
                limit=limit + 1  # +1 to account for self
            )
            
            # Filter out self
            results = [r for r in results if r.id != doc_id][:limit]
            
            # Format
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.payload.get("text", ""),
                    "metadata": {
                        k: v for k, v in r.payload.items()
                        if k not in ["text", "indexed_at"]
                    }
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Similar documents error: {e}")
            return []
    
    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from index"""
        
        try:
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=[doc_id]
            )
            logger.debug(f"Deleted document: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
    
    async def get_stats(self) -> Dict:
        """Get collection statistics"""
        
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            
            return {
                "total_documents": info.points_count,
                "vector_dimension": self.EMBEDDING_DIM,
                "status": info.status
            }
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}


# Global embedding service
embedding_service = EmbeddingService()