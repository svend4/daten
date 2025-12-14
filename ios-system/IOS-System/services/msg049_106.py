"""
Document Similarity Service
"""

import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import numpy as np

from .bert_client import bert_client
from .embeddings import embedding_service
from ..models import DocumentModel

logger = logging.getLogger(__name__)


class SimilarityService:
    """
    Document similarity and clustering
    
    Features:
    - Find duplicate documents
    - Group similar documents
    - Build document relationships
    - Identify outliers
    
    Usage:
        service = SimilarityService()
        
        # Find duplicates
        duplicates = await service.find_duplicates(threshold=0.95)
        
        # Cluster documents
        clusters = await service.cluster_documents(domain="SGB-IX")
    """
    
    async def find_duplicates(
        self,
        threshold: float = 0.95,
        domain: Optional[str] = None
    ) -> List[List[str]]:
        """
        Find duplicate or near-duplicate documents
        
        Args:
            threshold: Similarity threshold (0-1)
            domain: Optional domain filter
        
        Returns:
            List of duplicate groups
        """
        
        # TODO: Implement using all-pairs similarity
        # This is computationally expensive for large collections
        # Consider using LSH (Locality Sensitive Hashing) for scale
        
        logger.info(f"Finding duplicates (threshold={threshold})")
        
        # Placeholder implementation
        duplicates = []
        
        return duplicates
    
    async def compute_pairwise_similarity(
        self,
        doc_ids: List[str]
    ) -> np.ndarray:
        """
        Compute similarity matrix for documents
        
        Args:
            doc_ids: List of document IDs
        
        Returns:
            NxN similarity matrix
        """
        
        n = len(doc_ids)
        similarity_matrix = np.zeros((n, n))
        
        # Get all embeddings
        # This would require batch retrieval from Qdrant
        
        # Compute pairwise cosine similarity
        # similarity = embeddings @ embeddings.T
        
        return similarity_matrix
    
    async def get_related_documents(
        self,
        doc_id: str,
        max_results: int = 10,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Get documents related to given document
        
        Args:
            doc_id: Source document ID
            max_results: Max related documents
            min_similarity: Minimum similarity score
        
        Returns:
            List of related documents with scores
        """
        
        results = await embedding_service.get_similar_to_document(
            doc_id=doc_id,
            limit=max_results
        )
        
        # Filter by threshold
        results = [
            r for r in results
            if r["score"] >= min_similarity
        ]
        
        return results
    
    async def build_similarity_graph(
        self,
        doc_ids: List[str],
        threshold: float = 0.8
    ) -> Dict[str, List[Tuple[str, float]]]:
        """
        Build similarity graph
        
        Creates edges between documents with similarity > threshold
        
        Args:
            doc_ids: Documents to include
            threshold: Edge creation threshold
        
        Returns:
            Adjacency list: {doc_id: [(related_id, score), ...]}
        """
        
        graph = defaultdict(list)
        
        for doc_id in doc_ids:
            similar = await self.get_related_documents(
                doc_id=doc_id,
                max_results=20,
                min_similarity=threshold
            )
            
            for sim_doc in similar:
                graph[doc_id].append((sim_doc["id"], sim_doc["score"]))
        
        return dict(graph)
    
    async def identify_outliers(
        self,
        doc_ids: List[str],
        threshold: float = 0.5
    ) -> List[str]:
        """
        Identify outlier documents
        
        Outliers have low similarity to all other documents
        
        Args:
            doc_ids: Documents to analyze
            threshold: Average similarity threshold
        
        Returns:
            List of outlier document IDs
        """
        
        outliers = []
        
        for doc_id in doc_ids:
            similar = await embedding_service.get_similar_to_document(
                doc_id=doc_id,
                limit=10
            )
            
            if not similar:
                outliers.append(doc_id)
                continue
            
            # Calculate average similarity
            avg_similarity = np.mean([s["score"] for s in similar])
            
            if avg_similarity < threshold:
                outliers.append(doc_id)
        
        return outliers


# Global similarity service
similarity_service = SimilarityService()