"""
Neural Search API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field

from ios_core.search.neural_search import neural_search
from ios_core.search.search_analytics import search_analytics
from ios_core.search.multi_language import multi_language, Language
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class NeuralSearchRequest(BaseModel):
    query: str = Field(..., description="Search query", min_length=1)
    domain_filter: Optional[str] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    language: str = Field("de", regex="^(de|ru|en)$")
    enable_query_expansion: bool = True
    enable_personalization: bool = True
    semantic_weight: float = Field(0.6, ge=0.0, le=1.0)
    keyword_weight: float = Field(0.4, ge=0.0, le=1.0)


class SearchResult(BaseModel):
    id: str
    score: float
    final_score: float
    text: str
    metadata: dict
    highlights: Optional[dict] = None
    search_type: Optional[str] = None
    found_in_semantic: bool
    found_in_keyword: bool


class NeuralSearchResponse(BaseModel):
    query: str
    query_info: dict
    results: List[SearchResult]
    total: int
    limit: int
    offset: int
    execution_time_ms: int
    search_strategy: dict


class ClickEvent(BaseModel):
    search_id: str
    doc_id: str
    position: int
    time_to_click_ms: int


class SatisfactionFeedback(BaseModel):
    search_id: str
    satisfied: bool


@router.post("/search", response_model=NeuralSearchResponse)
@require_permission(Permission.DOCUMENT_READ)
async def neural_search_endpoint(
    request: NeuralSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Neural search combining semantic and keyword search
    
    Features:
    - Semantic similarity (BERT embeddings)
    - Keyword matching (Elasticsearch)
    - Hybrid ranking (ML-based fusion)
    - Query understanding & expansion
    - Multi-language support
    - Personalization
    
    Example:
        {
          "query": "Persönliches Budget beantragen",
          "limit": 20,
          "language": "de"
        }
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        # Update engine settings
        neural_search.semantic_weight = request.semantic_weight
        neural_search.keyword_weight = request.keyword_weight
        neural_search.enable_query_expansion = request.enable_query_expansion
        neural_search.enable_personalization = request.enable_personalization
        
        # Execute search
        results = await neural_search.search(
            query=request.query,
            user_id=current_user["id"],
            domain_filter=request.domain_filter,
            limit=request.limit,
            offset=request.offset,
            language=request.language
        )
        
        return NeuralSearchResponse(**results)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Neural search failed: {str(e)}"
        )


@router.get("/suggest")
@require_permission(Permission.DOCUMENT_READ)
async def get_suggestions(
    query: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    language: str = Query("de", regex="^(de|ru|en)$"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get query suggestions (autocomplete)
    
    Returns suggested queries based on partial input.
    
    Example:
        GET /suggest?query=Pers&limit=5
        
    Returns:
        ["Persönliches Budget", "Persönliche Assistenz", ...]
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        suggestions = await neural_search.suggest(
            query=query,
            limit=limit,
            language=language
        )
        
        return {
            "query": query,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Suggestion failed: {str(e)}"
        )


@router.post("/track/click")
@require_permission(Permission.DOCUMENT_READ)
async def track_click(
    event: ClickEvent,
    current_user: dict = Depends(get_current_user)
):
    """
    Track result click for analytics
    
    Call this when user clicks on a search result.
    Helps improve search quality through click tracking.
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        await search_analytics.log_click(
            search_id=event.search_id,
            doc_id=event.doc_id,
            position=event.position,
            time_to_click=event.time_to_click_ms
        )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Click tracking failed: {str(e)}"
        )


@router.post("/track/satisfaction")
@require_permission(Permission.DOCUMENT_READ)
async def track_satisfaction(
    feedback: SatisfactionFeedback,
    current_user: dict = Depends(get_current_user)
):
    """
    Track user satisfaction with search results
    
    Call this when user provides feedback on search quality.
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        await search_analytics.mark_satisfied(
            search_id=feedback.search_id,
            satisfied=feedback.satisfied
        )
        
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Satisfaction tracking failed: {str(e)}"
        )


@router.get("/analytics/metrics")
@require_permission(Permission.ADMIN_VIEW)
async def get_search_metrics(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """
    Get search quality metrics
    
    Returns analytics about search performance:
    - CTR (Click-Through Rate)
    - MRR (Mean Reciprocal Rank)
    - Zero results rate
    - Average execution time
    - Top queries
    - Intent distribution
    
    Requires: ADMIN_VIEW permission
    """
    
    from datetime import datetime, timedelta
    
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        metrics = await search_analytics.get_metrics(
            start_date=start_date,
            end_date=end_date
        )
        
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.get("/analytics/failed-queries")
@require_permission(Permission.ADMIN_VIEW)
async def get_failed_queries(
    days: int = Query(7, ge=1, le=30),
    min_count: int = Query(2, ge=1, le=10),
    current_user: dict = Depends(get_current_user)
):
    """
    Get queries that frequently return no results
    
    Helps identify content gaps and improve coverage.
    
    Requires: ADMIN_VIEW permission
    """
    
    try:
        failed = await search_analytics.get_failed_queries(
            days=days,
            min_count=min_count
        )
        
        return {
            "period_days": days,
            "min_count": min_count,
            "failed_queries": failed
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed queries retrieval failed: {str(e)}"
        )


@router.get("/analytics/slow-queries")
@require_permission(Permission.ADMIN_VIEW)
async def get_slow_queries(
    days: int = Query(7, ge=1, le=30),
    threshold_ms: int = Query(1000, ge=100, le=10000),
    current_user: dict = Depends(get_current_user)
):
    """
    Get slow queries for performance optimization
    
    Requires: ADMIN_VIEW permission
    """
    
    try:
        slow = await search_analytics.get_slow_queries(
            days=days,
            threshold_ms=threshold_ms
        )
        
        return {
            "period_days": days,
            "threshold_ms": threshold_ms,
            "slow_queries": slow
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Slow queries retrieval failed: {str(e)}"
        )


@router.post("/translate")
@require_permission(Permission.DOCUMENT_READ)
async def translate_query(
    query: str = Query(..., min_length=1),
    source_lang: Optional[str] = Query(None, regex="^(de|ru|en)$"),
    target_lang: str = Query("de", regex="^(de|ru|en)$"),
    current_user: dict = Depends(get_current_user)
):
    """
    Translate search query
    
    Supports cross-lingual search by translating queries.
    
    Example:
        POST /translate?query=Personal+budget&target_lang=de
        Returns: "Persönliches Budget"
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        # Convert to Language enum
        source = Language(source_lang) if source_lang else None
        target = Language(target_lang)
        
        translated = await multi_language.translate_query(
            query=query,
            source_lang=source,
            target_lang=target
        )
        
        # Detect language if not specified
        if source is None:
            source = multi_language.detect_language(query)
        
        return {
            "original": query,
            "translated": translated,
            "source_lang": source.value,
            "target_lang": target.value
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.get("/detect-language")
async def detect_language(
    text: str = Query(..., min_length=1)
):
    """
    Detect text language
    
    Returns detected language code (de, ru, en).
    """
    
    try:
        detected = multi_language.detect_language(text)
        
        return {
            "text": text,
            "language": detected.value,
            "confidence": "high"  # langdetect doesn't provide confidence
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        )