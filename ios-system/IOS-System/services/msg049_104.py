"""
BERT Model Client
"""

import logging
from typing import List, Dict, Optional
import asyncio

import httpx
import numpy as np

from ..config import settings

logger = logging.getLogger(__name__)


class BERTClient:
    """
    Client for BERT model server
    
    Usage:
        client = BERTClient()
        
        # Get embeddings
        embeddings = await client.embed(["Text 1", "Text 2"])
        
        # Extract entities
        entities = await client.extract_entities("Max Mustermann works at Bezirk Oberbayern")
        
        # Classify
        category = await client.classify("Widerspruch gegen Bescheid...")
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        timeout: int = 30
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def health_check(self) -> Dict:
        """Check BERT server health"""
        
        try:
            response = await self.client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"BERT health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def embed(
        self,
        texts: List[str],
        normalize: bool = True,
        pooling: str = "mean"
    ) -> List[List[float]]:
        """
        Get embeddings for texts
        
        Args:
            texts: List of texts to embed
            normalize: Normalize embeddings to unit length
            pooling: Pooling strategy (mean, max, cls)
        
        Returns:
            List of embedding vectors
        """
        
        try:
            response = await self.client.post(
                f"{self.base_url}/embed",
                json={
                    "texts": texts,
                    "normalize": normalize,
                    "pooling": pooling
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["embeddings"]
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    async def embed_single(
        self,
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """Get embedding for single text"""
        
        embeddings = await self.embed([text], normalize=normalize)
        return embeddings[0]
    
    async def extract_entities(
        self,
        text: str,
        threshold: float = 0.5
    ) -> List[Dict]:
        """
        Extract named entities
        
        Args:
            text: Input text
            threshold: Confidence threshold
        
        Returns:
            List of entities with type, text, score, position
        """
        
        try:
            response = await self.client.post(
                f"{self.base_url}/ner",
                json={
                    "text": text,
                    "threshold": threshold
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["entities"]
            
        except Exception as e:
            logger.error(f"NER error: {e}")
            raise
    
    async def classify(
        self,
        text: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Classify text
        
        Args:
            text: Input text
            top_k: Return top K predictions
        
        Returns:
            List of predictions with label and score
        """
        
        try:
            response = await self.client.post(
                f"{self.base_url}/classify",
                json={
                    "text": text,
                    "top_k": top_k
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["predictions"]
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return []
    
    async def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Compute semantic similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Cosine similarity (0-1)
        """
        
        try:
            response = await self.client.post(
                f"{self.base_url}/similarity",
                params={
                    "text1": text1,
                    "text2": text2
                }
            )
            response.raise_for_status()
            
            data = response.json()
            return data["similarity"]
            
        except Exception as e:
            logger.error(f"Similarity error: {e}")
            return 0.0
    
    async def close(self):
        """Close client"""
        await self.client.aclose()


# Global BERT client
bert_client = BERTClient(base_url=settings.bert_service_url)