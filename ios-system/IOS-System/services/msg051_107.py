"""
Semantic Search API
Uses BERT embeddings for neural search
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from ios_core.ml.bert_client import bert_client
from ios_core.ml.embeddings import embedding_service
from ios_core.ml.similarity import similarity_service
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(10, ge=1, le=100)
    domain_filter: Optional[str] = None
    score_threshold: float = Field(0.7, ge=0.0, le=1.0)


class SemanticSearchResult(BaseModel):
    id: str
    score: float
    text: str
    metadata: dict


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
    total: int
    execution_time_ms: int


class SimilarDocumentsRequest(BaseModel):
    document_id: str
    limit: int = Field(10, ge=1, le=50)
    min_similarity: float = Field(0.7, ge=0.0, le=1.0)


class EntityExtractionRequest(BaseModel):
    text: str
    threshold: float = Field(0.5, ge=0.0, le=1.0)


class EntityExtractionResponse(BaseModel):
    entities: List[dict]
    text: str


@router.post("/search", response_model=SemanticSearchResponse)
@require_permission(Permission.DOCUMENT_READ)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Semantic search using BERT embeddings
    
    Finds documents based on meaning, not just keywords.
    
    Example:
        Query: "Persönliches Budget"
        Finds: Documents about personal budgets, even if they use
               different terminology like "individuelle Leistungen"
    
    Requires: DOCUMENT_READ permission
    """
    
    import time
    start = time.time()
    
    try:
        # Search similar documents
        results = await embedding_service.search_similar(
            query=request.query,
            limit=request.limit,
            domain_filter=request.domain_filter,
            score_threshold=request.score_threshold
        )
        
        execution_time = int((time.time() - start) * 1000)
        
        return SemanticSearchResponse(
            query=request.query,
            results=[
                SemanticSearchResult(
                    id=r["id"],
                    score=r["score"],
                    text=r["text"],
                    metadata=r["metadata"]
                )
                for r in results
            ],
            total=len(results),
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}"
        )


@router.post("/similar-documents", response_model=List[SemanticSearchResult])
@require_permission(Permission.DOCUMENT_READ)
async def find_similar_documents(
    request: SimilarDocumentsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Find documents similar to a given document
    
    Uses semantic similarity to find related documents.
    Useful for:
    - Finding related case law
    - Discovering similar templates
    - Building document clusters
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        results = await similarity_service.get_related_documents(
            doc_id=request.document_id,
            max_results=request.limit,
            min_similarity=request.min_similarity
        )
        
        return [
            SemanticSearchResult(
                id=r["id"],
                score=r["score"],
                text=r["text"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Similar documents search failed: {str(e)}"
        )


@router.post("/extract-entities", response_model=EntityExtractionResponse)
@require_permission(Permission.DOCUMENT_READ)
async def extract_entities(
    request: EntityExtractionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Extract named entities from text
    
    Recognizes:
    - PER: Person names
    - ORG: Organizations (courts, agencies)
    - LOC: Locations
    - MISC: Miscellaneous (laws, dates, amounts)
    
    Example:
        Input: "Max Mustermann beantragt beim Bezirk Oberbayern..."
        Output: [
            {"entity": "PER", "text": "Max Mustermann", "score": 0.95},
            {"entity": "ORG", "text": "Bezirk Oberbayern", "score": 0.92}
        ]
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        entities = await bert_client.extract_entities(
            text=request.text,
            threshold=request.threshold
        )
        
        return EntityExtractionResponse(
            entities=entities,
            text=request.text
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.get("/embeddings/stats")
@require_permission(Permission.DOCUMENT_READ)
async def get_embedding_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Get embedding service statistics
    
    Returns information about indexed documents and vector dimensions.
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        stats = await embedding_service.get_stats()
        health = await bert_client.health_check()
        
        return {
            "embedding_service": stats,
            "bert_service": health
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stats retrieval failed: {str(e)}"
        )


@router.post("/compute-similarity")
@require_permission(Permission.DOCUMENT_READ)
async def compute_text_similarity(
    text1: str,
    text2: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Compute semantic similarity between two texts
    
    Returns cosine similarity score (0-1):
    - 0.0-0.3: Not similar
    - 0.3-0.6: Somewhat similar
    - 0.6-0.8: Similar
    - 0.8-1.0: Very similar
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        similarity = await bert_client.compute_similarity(text1, text2)
        
        # Classify similarity level
        if similarity >= 0.8:
            level = "very_similar"
        elif similarity >= 0.6:
            level = "similar"
        elif similarity >= 0.3:
            level = "somewhat_similar"
        else:
            level = "not_similar"
        
        return {
            "similarity": similarity,
            "level": level,
            "text1_length": len(text1),
            "text2_length": len(text2)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Similarity computation failed: {str(e)}"
        )