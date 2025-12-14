"""
Cache Management API Endpoints
Admin endpoints for cache control
"""

from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ios_core.cache.multi_level_cache import (
    get_cache,
    CacheWarmer,
    CacheInvalidator
)
from ios_core.cdn.cdn_integration import get_cdn_manager
from ..dependencies import require_admin

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheStats(BaseModel):
    """Cache statistics response"""
    l1: Dict
    l2: Dict
    timestamp: str


class CacheClearRequest(BaseModel):
    """Cache clear request"""
    pattern: str = "*"


class CacheWarmRequest(BaseModel):
    """Cache warming request"""
    document_limit: int = 100
    search_queries: list[str] = []


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    _: str = Depends(require_admin)
):
    """
    Get cache statistics
    
    Returns hit rates, sizes, and performance metrics
    """
    from datetime import datetime
    
    cache = get_cache()
    stats = cache.stats()
    
    return CacheStats(
        l1=stats["l1"],
        l2=stats["l2"],
        timestamp=datetime.now().isoformat()
    )


@router.post("/clear")
async def clear_cache(
    request: CacheClearRequest,
    _: str = Depends(require_admin)
):
    """
    Clear cache
    
    Can clear all or specific pattern
    """
    cache = get_cache()
    
    if request.pattern == "*":
        cache.clear()
        return {"message": "All caches cleared"}
    else:
        cache.delete_pattern(request.pattern)
        return {"message": f"Caches cleared for pattern: {request.pattern}"}


@router.post("/invalidate/document/{document_id}")
async def invalidate_document_cache(
    document_id: int,
    _: str = Depends(require_admin)
):
    """Invalidate cache for specific document"""
    cache = get_cache()
    invalidator = CacheInvalidator(cache)
    
    invalidator.invalidate_document(document_id)
    
    return {"message": f"Cache invalidated for document {document_id}"}


@router.post("/invalidate/user/{user_id}")
async def invalidate_user_cache(
    user_id: int,
    _: str = Depends(require_admin)
):
    """Invalidate cache for specific user"""
    cache = get_cache()
    invalidator = CacheInvalidator(cache)
    
    invalidator.invalidate_user(user_id)
    
    return {"message": f"Cache invalidated for user {user_id}"}


@router.post("/invalidate/search")
async def invalidate_search_cache(
    _: str = Depends(require_admin)
):
    """Invalidate all search result caches"""
    cache = get_cache()
    invalidator = CacheInvalidator(cache)
    
    invalidator.invalidate_search()
    
    return {"message": "Search caches invalidated"}


@router.post("/warm")
async def warm_cache(
    request: CacheWarmRequest,
    _: str = Depends(require_admin)
):
    """
    Warm cache with frequently accessed data
    
    Preloads popular documents and search results
    """
    cache = get_cache()
    warmer = CacheWarmer(cache)
    
    # Warm documents
    await warmer.warm_popular_documents(limit=request.document_limit)
    
    # Warm search results
    if request.search_queries:
        await warmer.warm_search_results(request.search_queries)
    
    return {
        "message": "Cache warming completed",
        "documents": request.document_limit,
        "searches": len(request.search_queries)
    }


@router.get("/cdn/status")
async def get_cdn_status(
    _: str = Depends(require_admin)
):
    """Get CDN status and configuration"""
    from ios_core.config import settings
    
    return {
        "enabled": settings.cdn_enabled,
        "provider": settings.cdn_provider,
        "domain": settings.cdn_domain
    }


@router.post("/cdn/purge")
async def purge_cdn(
    paths: list[str],
    _: str = Depends(require_admin)
):
    """Purge specific assets from CDN"""
    cdn = get_cdn_manager()
    
    success = cdn.purge_assets(paths)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CDN purge failed"
        )
    
    return {
        "message": f"Purged {len(paths)} assets from CDN",
        "paths": paths
    }


@router.post("/cdn/purge-all")
async def purge_cdn_all(
    _: str = Depends(require_admin)
):
    """Purge entire CDN cache"""
    cdn = get_cdn_manager()
    
    success = cdn.purge_all()
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CDN purge failed"
        )
    
    return {"message": "All CDN cache purged"}


@router.post("/cdn/warm")
async def warm_cdn(
    paths: list[str],
    _: str = Depends(require_admin)
):
    """Warm CDN cache by prefetching assets"""
    cdn = get_cdn_manager()
    
    success = cdn.warm_cache(paths)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CDN warming failed"
        )
    
    return {
        "message": f"Warmed {len(paths)} assets in CDN",
        "paths": paths
    }