"""
Search routes
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ios_core.system import IOSSystem
from ..dependencies import get_ios_system, get_current_active_user

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    domain_name: Optional[str] = Field(None, description="Domain to search in")
    search_type: str = Field(default="hybrid", description="Type: full_text, semantic, hybrid")
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class SearchResult(BaseModel):
    doc_id: str
    title: str
    document_type: str
    score: float
    highlights: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_count: int
    query: str
    search_time_ms: float


@router.post("/", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Search for documents
    
    **Search types:**
    - `full_text`: Traditional keyword search (BM25)
    - `semantic`: Meaning-based search (TF-IDF + cosine similarity)
    - `hybrid`: Combines both approaches
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8000/api/search/" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "Persönliches Budget",
        "domain_name": "SGB-IX",
        "search_type": "hybrid",
        "limit": 10
      }'
    ```
    """
    import time
    start_time = time.time()
    
    results = await ios.search_documents(
        query=request.query,
        domain_name=request.domain_name,
        search_type=request.search_type,
        limit=request.limit,
        offset=request.offset
    )
    
    search_time = (time.time() - start_time) * 1000
    
    return SearchResponse(
        results=[SearchResult(**r) for r in results.get('results', [])],
        total_count=results.get('total_count', 0),
        query=request.query,
        search_time_ms=search_time
    )


@router.get("/suggest", response_model=List[str])
async def autocomplete(
    prefix: str = Query(..., min_length=2, description="Search prefix"),
    domain_name: Optional[str] = Query(None, description="Domain to search in"),
    max_suggestions: int = Query(default=10, ge=1, le=50),
    ios: IOSSystem = Depends(get_ios_system),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Get autocomplete suggestions
    
    **Example:**
    ```bash
    curl "http://localhost:8000/api/search/suggest?prefix=Pers&max_suggestions=5" \
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    # TODO: Implement autocomplete in SearchService
    return [
        f"{prefix}önliches Budget",
        f"{prefix}onal",
        f"{prefix}onalausweis"
    ][:max_suggestions]