"""
Search Resource
"""

from typing import List, Optional, Dict
from ..models import SearchResult


class SearchResource:
    """
    Search API resource
    
    Example:
        >>> # Basic search
        >>> results = client.search.query("personal budget")
        >>> for result in results:
        ...     print(result.title, result.score)
        
        >>> # Neural search
        >>> results = client.search.neural(
        ...     query="Persönliches Budget",
        ...     limit=10
        ... )
        
        >>> # Semantic search
        >>> results = client.search.semantic(
        ...     query="budget for disabled people",
        ...     threshold=0.8
        ... )
    """
    
    def __init__(self, client):
        self.client = client
    
    def query(
        self,
        query: str,
        limit: int = 10,
        domain_id: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Basic search
        
        Args:
            query: Search query
            limit: Max results
            domain_id: Filter by domain
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit
        }
        
        if domain_id:
            params["domain_id"] = domain_id
        
        response = self.client.get("/api/search", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]
    
    def neural(
        self,
        query: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Neural search (semantic + keyword hybrid)
        
        Args:
            query: Search query
            limit: Max results
            score_threshold: Minimum score
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit,
            "score_threshold": score_threshold
        }
        
        response = self.client.get("/api/search/neural", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]
    
    def semantic(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.8
    ) -> List[SearchResult]:
        """
        Semantic search (embeddings only)
        
        Args:
            query: Search query
            limit: Max results
            threshold: Similarity threshold
            
        Returns:
            Search results
        """
        
        params = {
            "query": query,
            "limit": limit,
            "threshold": threshold
        }
        
        response = self.client.get("/api/semantic/search", params=params)
        
        return [
            SearchResult.from_dict(result)
            for result in response.get("results", [])
        ]