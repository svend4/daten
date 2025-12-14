"""
Documents Resource
"""

from typing import List, Optional, Dict, Any
from ..models import Document


class DocumentsResource:
    """
    Documents API resource
    
    Example:
        >>> docs = client.documents.list(limit=10)
        >>> doc = client.documents.create(
        ...     title="My Doc",
        ...     content="Content"
        ... )
        >>> doc = client.documents.get("doc_123")
        >>> client.documents.update("doc_123", title="Updated")
        >>> client.documents.delete("doc_123")
    """
    
    def __init__(self, client):
        self.client = client
    
    def list(
        self,
        limit: int = 50,
        offset: int = 0,
        domain_id: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Document]:
        """
        List documents
        
        Args:
            limit: Max documents to return
            offset: Pagination offset
            domain_id: Filter by domain
            search: Search query
            
        Returns:
            List of documents
        """
        
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if domain_id:
            params["domain_id"] = domain_id
        
        if search:
            params["search"] = search
        
        response = self.client.get("/api/documents", params=params)
        
        return [
            Document.from_dict(doc)
            for doc in response.get("documents", [])
        ]
    
    def get(self, document_id: str) -> Document:
        """
        Get document by ID
        
        Args:
            document_id: Document ID
            
        Returns:
            Document
        """
        
        response = self.client.get(f"/api/documents/{document_id}")
        return Document.from_dict(response)
    
    def create(
        self,
        title: str,
        content: str,
        domain_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        Create document
        
        Args:
            title: Document title
            content: Document content
            domain_id: Domain ID
            metadata: Additional metadata
            
        Returns:
            Created document
        """
        
        data = {
            "title": title,
            "content": content
        }
        
        if domain_id:
            data["domain_id"] = domain_id
        
        if metadata:
            data["metadata"] = metadata
        
        response = self.client.post("/api/documents", json=data)
        return Document.from_dict(response)
    
    def update(
        self,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Document:
        """
        Update document
        
        Args:
            document_id: Document ID
            title: New title
            content: New content
            metadata: New metadata
            
        Returns:
            Updated document
        """
        
        data = {}
        
        if title is not None:
            data["title"] = title
        
        if content is not None:
            data["content"] = content
        
        if metadata is not None:
            data["metadata"] = metadata
        
        response = self.client.patch(
            f"/api/documents/{document_id}",
            json=data
        )
        
        return Document.from_dict(response)
    
    def delete(self, document_id: str) -> bool:
        """
        Delete document
        
        Args:
            document_id: Document ID
            
        Returns:
            True if deleted
        """
        
        self.client.delete(f"/api/documents/{document_id}")
        return True