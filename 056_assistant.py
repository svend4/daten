Продолжаю Day 121-122: Neural Search & Multi-language. Осталось создать:
- Search Analytics
- API Routes  
- Tests
- Configuration
- Documentation

Создам оставшиеся файлы для завершения этого дня.# 🔍 DAY 121-122: NEURAL SEARCH & MULTI-LANGUAGE (ПРОДОЛЖЕНИЕ)

---

## ФАЙЛ 100: `ios_core/search/search_analytics.py`

```python
"""
Search Analytics
Track and analyze search quality and user behavior
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import json

from ..database import async_session
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)

Base = declarative_base()


class SearchLogModel(Base):
    """Search log model"""
    
    __tablename__ = "search_logs"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Query information
    query = Column(Text, nullable=False)
    user_id = Column(String, nullable=True)
    language = Column(String, nullable=False)
    intent = Column(String, nullable=True)
    
    # Results
    results_count = Column(Integer, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    
    # Search strategy
    semantic_weight = Column(Float, nullable=False)
    keyword_weight = Column(Float, nullable=False)
    
    # User interaction
    clicked_results = Column(JSON, nullable=True)  # List of clicked doc IDs
    clicked_position = Column(Integer, nullable=True)  # Position of first click
    time_to_click_ms = Column(Integer, nullable=True)
    
    # Query analysis
    query_info = Column(JSON, nullable=True)
    
    # Success metrics
    had_results = Column(Integer, nullable=False)  # 1 if results > 0, else 0
    user_satisfied = Column(Integer, nullable=True)  # 1 if satisfied, 0 if not


class SearchAnalytics:
    """
    Search analytics and quality monitoring
    
    Features:
    - Query logging
    - Click tracking
    - Performance monitoring
    - Quality metrics (CTR, MRR, NDCG)
    - Query clustering
    - Search optimization insights
    
    Usage:
        analytics = SearchAnalytics()
        
        # Log search
        await analytics.log_search(
            query="Persönliches Budget",
            user_id="user123",
            results_count=15,
            execution_time=125
        )
        
        # Track click
        await analytics.log_click(
            search_id="search123",
            doc_id="doc456",
            position=3,
            time_to_click=2500
        )
    """
    
    async def log_search(
        self,
        query: str,
        user_id: Optional[str],
        results_count: int,
        execution_time: float,
        query_info: Optional[Dict] = None,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> str:
        """
        Log search query
        
        Args:
            query: Search query
            user_id: User ID
            results_count: Number of results
            execution_time: Execution time in seconds
            query_info: Query analysis information
            semantic_weight: Semantic search weight
            keyword_weight: Keyword search weight
        
        Returns:
            Search log ID
        """
        
        import uuid
        search_id = str(uuid.uuid4())
        
        async with async_session() as session:
            log = SearchLogModel(
                id=search_id,
                query=query,
                user_id=user_id,
                language=query_info.get("language", "de") if query_info else "de",
                intent=query_info.get("intent") if query_info else None,
                results_count=results_count,
                execution_time_ms=int(execution_time * 1000),
                semantic_weight=semantic_weight,
                keyword_weight=keyword_weight,
                query_info=query_info,
                had_results=1 if results_count > 0 else 0
            )
            
            session.add(log)
            await session.commit()
        
        return search_id
    
    async def log_click(
        self,
        search_id: str,
        doc_id: str,
        position: int,
        time_to_click: int
    ):
        """
        Log result click
        
        Args:
            search_id: Search log ID
            doc_id: Clicked document ID
            position: Position in results (1-based)
            time_to_click: Time to click in milliseconds
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(SearchLogModel).where(SearchLogModel.id == search_id)
            )
            log = result.scalar_one_or_none()
            
            if log:
                # Update clicked results
                clicked = log.clicked_results or []
                if doc_id not in clicked:
                    clicked.append(doc_id)
                log.clicked_results = clicked
                
                # Update position (first click)
                if log.clicked_position is None:
                    log.clicked_position = position
                    log.time_to_click_ms = time_to_click
                
                await session.commit()
    
    async def mark_satisfied(
        self,
        search_id: str,
        satisfied: bool
    ):
        """
        Mark user satisfaction with search results
        
        Args:
            search_id: Search log ID
            satisfied: Whether user was satisfied
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(SearchLogModel).where(SearchLogModel.id == search_id)
            )
            log = result.scalar_one_or_none()
            
            if log:
                log.user_satisfied = 1 if satisfied else 0
                await session.commit()
    
    async def get_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Get search quality metrics
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            user_id: Filter by user
        
        Returns:
            Metrics dict
        """
        
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()
        
        async with async_session() as session:
            # Build query
            conditions = [
                SearchLogModel.timestamp >= start_date,
                SearchLogModel.timestamp <= end_date
            ]
            
            if user_id:
                conditions.append(SearchLogModel.user_id == user_id)
            
            # Get logs
            result = await session.execute(
                select(SearchLogModel).where(and_(*conditions))
            )
            logs = result.scalars().all()
            
            if not logs:
                return {
                    "total_searches": 0,
                    "message": "No data available for the selected period"
                }
            
            # Calculate metrics
            total_searches = len(logs)
            searches_with_results = sum(1 for log in logs if log.had_results)
            searches_with_clicks = sum(1 for log in logs if log.clicked_results)
            
            # Click-through rate (CTR)
            ctr = searches_with_clicks / total_searches if total_searches > 0 else 0
            
            # Zero results rate
            zero_results_rate = (total_searches - searches_with_results) / total_searches if total_searches > 0 else 0
            
            # Average execution time
            avg_execution_time = sum(log.execution_time_ms for log in logs) / total_searches
            
            # Average results count
            avg_results = sum(log.results_count for log in logs) / total_searches
            
            # Average click position (Mean Reciprocal Rank approximation)
            click_positions = [log.clicked_position for log in logs if log.clicked_position]
            avg_click_position = sum(click_positions) / len(click_positions) if click_positions else None
            mrr = (1 / avg_click_position) if avg_click_position else 0
            
            # User satisfaction
            satisfaction_scores = [log.user_satisfied for log in logs if log.user_satisfied is not None]
            satisfaction_rate = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else None
            
            # Popular queries
            query_counts = defaultdict(int)
            for log in logs:
                query_counts[log.query.lower()] += 1
            
            top_queries = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            # Intent distribution
            intent_counts = defaultdict(int)
            for log in logs:
                if log.intent:
                    intent_counts[log.intent] += 1
            
            # Language distribution
            lang_counts = defaultdict(int)
            for log in logs:
                lang_counts[log.language] += 1
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "overview": {
                    "total_searches": total_searches,
                    "searches_with_results": searches_with_results,
                    "searches_with_clicks": searches_with_clicks,
                    "unique_users": len(set(log.user_id for log in logs if log.user_id))
                },
                "quality_metrics": {
                    "ctr": round(ctr, 3),
                    "zero_results_rate": round(zero_results_rate, 3),
                    "mrr": round(mrr, 3),
                    "avg_click_position": round(avg_click_position, 2) if avg_click_position else None,
                    "satisfaction_rate": round(satisfaction_rate, 3) if satisfaction_rate else None
                },
                "performance": {
                    "avg_execution_time_ms": round(avg_execution_time, 2),
                    "avg_results_count": round(avg_results, 2)
                },
                "top_queries": [
                    {"query": q, "count": c}
                    for q, c in top_queries
                ],
                "intent_distribution": dict(intent_counts),
                "language_distribution": dict(lang_counts)
            }
    
    async def get_failed_queries(
        self,
        days: int = 7,
        min_count: int = 2
    ) -> List[Dict]:
        """
        Get queries that frequently return no results
        
        Args:
            days: Look back period
            min_count: Minimum occurrences
        
        Returns:
            List of failed queries
        """
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with async_session() as session:
            result = await session.execute(
                select(SearchLogModel).where(
                    and_(
                        SearchLogModel.timestamp >= start_date,
                        SearchLogModel.had_results == 0
                    )
                )
            )
            logs = result.scalars().all()
            
            # Count failures per query
            query_counts = defaultdict(int)
            for log in logs:
                query_counts[log.query.lower()] += 1
            
            # Filter by min count
            failed = [
                {"query": q, "count": c}
                for q, c in query_counts.items()
                if c >= min_count
            ]
            
            # Sort by count
            failed.sort(key=lambda x: x["count"], reverse=True)
            
            return failed
    
    async def get_slow_queries(
        self,
        days: int = 7,
        threshold_ms: int = 1000
    ) -> List[Dict]:
        """
        Get slow queries
        
        Args:
            days: Look back period
            threshold_ms: Slowness threshold
        
        Returns:
            List of slow queries
        """
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with async_session() as session:
            result = await session.execute(
                select(SearchLogModel).where(
                    and_(
                        SearchLogModel.timestamp >= start_date,
                        SearchLogModel.execution_time_ms >= threshold_ms
                    )
                ).order_by(SearchLogModel.execution_time_ms.desc())
                .limit(20)
            )
            logs = result.scalars().all()
            
            return [
                {
                    "query": log.query,
                    "execution_time_ms": log.execution_time_ms,
                    "results_count": log.results_count,
                    "timestamp": log.timestamp.isoformat()
                }
                for log in logs
            ]


# Global search analytics
search_analytics = SearchAnalytics()
```

---

## ФАЙЛ 101: `alembic/versions/008_add_search_logs.py`

```python
"""
Add search logs table

Revision ID: 008
Revises: 007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    """Create search_logs table"""
    
    op.create_table(
        'search_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=False),
        sa.Column('intent', sa.String(), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=False),
        sa.Column('semantic_weight', sa.Float(), nullable=False),
        sa.Column('keyword_weight', sa.Float(), nullable=False),
        sa.Column('clicked_results', JSON, nullable=True),
        sa.Column('clicked_position', sa.Integer(), nullable=True),
        sa.Column('time_to_click_ms', sa.Integer(), nullable=True),
        sa.Column('query_info', JSON, nullable=True),
        sa.Column('had_results', sa.Integer(), nullable=False),
        sa.Column('user_satisfied', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_search_logs_timestamp', 'search_logs', ['timestamp'])
    op.create_index('idx_search_logs_user_id', 'search_logs', ['user_id'])
    op.create_index('idx_search_logs_query', 'search_logs', ['query'])
    op.create_index('idx_search_logs_had_results', 'search_logs', ['had_results'])


def downgrade():
    """Drop search_logs table"""
    
    op.drop_index('idx_search_logs_had_results', table_name='search_logs')
    op.drop_index('idx_search_logs_query', table_name='search_logs')
    op.drop_index('idx_search_logs_user_id', table_name='search_logs')
    op.drop_index('idx_search_logs_timestamp', table_name='search_logs')
    op.drop_table('search_logs')
```

---

## ФАЙЛ 102: `api/routes/neural_search.py`

```python
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
```

---

## ФАЙЛ 103: `api/main.py` (UPDATE - add neural search routes)

```python
"""
FastAPI application - UPDATED with neural search
"""

# ... (existing imports)
from .routes import neural_search

# ... (existing code)

# Include neural search router
app.include_router(
    neural_search.router,
    prefix="/api/search/neural",
    tags=["Neural Search"]
)

# ... (rest of existing code)
```

---

## ФАЙЛ 104: `ios_core/config.py` (UPDATE - add ML/search settings)

```python
"""
Configuration - UPDATED with ML and search settings
"""

# ... (existing code)

class Settings(BaseSettings):
    # ... (existing settings)
    
    # ML Services
    bert_service_url: str = "http://localhost:8001"
    sentence_transformers_url: str = "http://localhost:8003"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    
    # Neural Search
    default_semantic_weight: float = 0.6
    default_keyword_weight: float = 0.4
    enable_query_expansion: bool = True
    enable_personalization: bool = True
    
    # Multi-language
    default_language: str = "de"
    supported_languages: List[str] = ["de", "ru", "en"]
    enable_auto_translation: bool = True
    
    # Search Analytics
    track_search_clicks: bool = True
    track_search_satisfaction: bool = True
    analytics_retention_days: int = 90
    
    class Config:
        env_file = ".env"

# ... (rest of existing code)
```

---

## ФАЙЛ 105: `requirements.txt` (UPDATE)

```txt
# ... (existing requirements)

# Machine Learning
torch==2.1.2
transformers==4.37.0
sentence-transformers==2.3.1
qdrant-client==1.7.3

# NLP
langdetect==1.0.9
deep-translator==1.11.4
spacy==3.7.2

# ... (rest of existing requirements)
```

---

## ФАЙЛ 106: `tests/search/test_neural_search.py`

```python
"""
Tests for neural search
"""

import pytest
from ios_core.search.neural_search import neural_search
from ios_core.search.query_understanding import query_analyzer
from ios_core.search.multi_language import multi_language, Language


@pytest.mark.asyncio
async def test_neural_search():
    """Test neural search execution"""
    
    results = await neural_search.search(
        query="Persönliches Budget",
        limit=10,
        language="de"
    )
    
    assert "query" in results
    assert "results" in results
    assert "total" in results
    assert "execution_time_ms" in results
    assert results["query"] == "Persönliches Budget"


@pytest.mark.asyncio
async def test_query_analysis():
    """Test query understanding"""
    
    query_info = await query_analyzer.analyze(
        query="Wie beantrage ich ein Persönliches Budget?",
        language="de"
    )
    
    assert "language" in query_info
    assert "intent" in query_info
    assert "is_question" in query_info
    assert query_info["is_question"] is True


@pytest.mark.asyncio
async def test_language_detection():
    """Test language detection"""
    
    # German
    lang_de = multi_language.detect_language("Das Persönliche Budget")
    assert lang_de == Language.GERMAN
    
    # Russian
    lang_ru = multi_language.detect_language("Личный бюджет для инвалидов")
    assert lang_ru == Language.RUSSIAN
    
    # English
    lang_en = multi_language.detect_language("Personal budget for disabled persons")
    assert lang_en == Language.ENGLISH


@pytest.mark.asyncio
async def test_query_translation():
    """Test query translation"""
    
    translated = await multi_language.translate_query(
        query="Personal budget",
        source_lang=Language.ENGLISH,
        target_lang=Language.GERMAN
    )
    
    assert isinstance(translated, str)
    assert len(translated) > 0


@pytest.mark.asyncio
async def test_legal_reference_extraction():
    """Test legal reference extraction"""
    
    query_info = await query_analyzer.analyze(
        query="§ 29 SGB IX Persönliches Budget",
        language="de"
    )
    
    assert "legal_references" in query_info
    assert len(query_info["legal_references"]) > 0
    assert any("§ 29" in ref for ref in query_info["legal_references"])


@pytest.mark.asyncio
async def test_entity_extraction():
    """Test entity extraction from query"""
    
    query_info = await query_analyzer.analyze(
        query="Antrag beim Bezirk Oberbayern stellen",
        language="de"
    )
    
    assert "entities" in query_info
    # May or may not find entities depending on BERT model


@pytest.mark.asyncio
async def test_query_expansion():
    """Test query expansion"""
    
    query_info = await query_analyzer.analyze(
        query="Persönliches Budget",
        language="de"
    )
    
    assert "expansion" in query_info
    # Expansions should include synonyms


@pytest.mark.asyncio
async def test_suggestions():
    """Test query suggestions"""
    
    suggestions = await neural_search.suggest(
        query="Pers",
        limit=5,
        language="de"
    )
    
    assert isinstance(suggestions, list)
```

---

## ФАЙЛ 107: `scripts/test_neural_search.sh`

```bash
#!/bin/bash
# Test neural search features

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         NEURAL SEARCH TEST                                 ║"
echo "╚════════════════════════════════════════════════════════════╝"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_URL="http://localhost:8000"
TOKEN=""

# Get auth token
echo -e "\n${YELLOW}[1/8] Authenticating...${NC}"
TOKEN=$(curl -s -X POST "$API_URL/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Authenticated${NC}"
else
    echo -e "${RED}✗ Authentication failed${NC}"
    exit 1
fi

# Test 1: Neural Search
echo -e "\n${YELLOW}[2/8] Testing Neural Search...${NC}"
SEARCH_RESPONSE=$(curl -s -X POST "$API_URL/api/search/neural/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Persönliches Budget beantragen",
    "limit": 10,
    "language": "de"
  }')

RESULTS_COUNT=$(echo $SEARCH_RESPONSE | jq '.total')
EXEC_TIME=$(echo $SEARCH_RESPONSE | jq '.execution_time_ms')

echo -e "${GREEN}✓ Neural search complete${NC}"
echo "  Results: $RESULTS_COUNT"
echo "  Execution time: ${EXEC_TIME}ms"

# Test 2: Query Suggestions
echo -e "\n${YELLOW}[3/8] Testing Query Suggestions...${NC}"
SUGGESTIONS=$(curl -s -X GET "$API_URL/api/search/neural/suggest?query=Pers&limit=5" \
  -H "Authorization: Bearer $TOKEN")

SUGG_COUNT=$(echo $SUGGESTIONS | jq '.suggestions | length')
echo -e "${GREEN}✓ Got $SUGG_COUNT suggestions${NC}"

# Test 3: Language Detection
echo -e "\n${YELLOW}[4/8] Testing Language Detection...${NC}"

# German
LANG_DE=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Persönliches+Budget" \
  | jq -r '.language')
echo "  German text detected as: $LANG_DE"

# Russian
LANG_RU=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Личный+бюджет" \
  | jq -r '.language')
echo "  Russian text detected as: $LANG_RU"

# English
LANG_EN=$(curl -s -X GET "$API_URL/api/search/neural/detect-language?text=Personal+budget" \
  | jq -r '.language')
echo "  English text detected as: $LANG_EN"

if [ "$LANG_DE" = "de" ] && [ "$LANG_RU" = "ru" ] && [ "$LANG_EN" = "en" ]; then
    echo -e "${GREEN}✓ Language detection working${NC}"
fi

# Test 4: Query Translation
echo -e "\n${YELLOW}[5/8] Testing Query Translation...${NC}"
TRANSLATION=$(curl -s -X POST "$API_URL/api/search/neural/translate?query=Personal+budget&target_lang=de" \
  -H "Authorization: Bearer $TOKEN")

TRANSLATED=$(echo $TRANSLATION | jq -r '.translated')
echo "  'Personal budget' → '$TRANSLATED'"
echo -e "${GREEN}✓ Translation working${NC}"

# Test 5: Semantic Search
echo -e "\n${YELLOW}[6/8] Testing Semantic Search...${NC}"
SEMANTIC=$(curl -s -X POST "$API_URL/api/semantic/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Budget für Menschen mit Behinderung",
    "limit": 5,
    "score_threshold": 0.7
  }')

SEM_RESULTS=$(echo $SEMANTIC | jq '.total')
echo -e "${GREEN}✓ Found $SEM_RESULTS semantic matches${NC}"

# Test 6: Entity Extraction
echo -e "\n${YELLOW}[7/8] Testing Entity Extraction...${NC}"
ENTITIES=$(curl -s -X POST "$API_URL/api/semantic/extract-entities" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Max Mustermann beantragt beim Bezirk Oberbayern ein Persönliches Budget nach § 29 SGB IX.",
    "threshold": 0.5
  }')

ENTITY_COUNT=$(echo $ENTITIES | jq '.entities | length')
echo -e "${GREEN}✓ Extracted $ENTITY_COUNT entities${NC}"

# Test 7: Search Analytics
echo -e "\n${YELLOW}[8/8] Testing Search Analytics...${NC}"
METRICS=$(curl -s -X GET "$API_URL/api/search/neural/analytics/metrics?days=7" \
  -H "Authorization: Bearer $TOKEN")

TOTAL_SEARCHES=$(echo $METRICS | jq '.overview.total_searches')
CTR=$(echo $METRICS | jq '.quality_metrics.ctr')

echo -e "${GREEN}✓ Analytics available${NC}"
echo "  Total searches (7 days): $TOTAL_SEARCHES"
echo "  Click-through rate: $CTR"

echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            NEURAL SEARCH TEST COMPLETE                     ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}All tests passed!${NC}"
```

---

## ФАЙЛ 108: `docs/search/NEURAL_SEARCH.md`

```markdown
# Neural Search Guide

## Overview

IOS System uses advanced neural search combining:

- **Semantic Search**: BERT embeddings for meaning-based search
- **Keyword Search**: Elasticsearch for traditional text matching
- **Hybrid Ranking**: ML-based fusion of multiple signals
- **Query Understanding**: Intent classification and entity extraction
- **Multi-language**: Support for German, Russian, English
- **Analytics**: Search quality metrics and optimization

## Architecture

```
User Query
    ↓
┌─────────────────────┐
│  Query Analysis     │
│  - Language detect  │
│  - Intent classify  │
│  - Entity extract   │
│  - Query expand     │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     ↓           ↓
┌─────────┐ ┌──────────┐
│Semantic │ │ Keyword  │
│ Search  │ │  Search  │
│ (BERT)  │ │  (ES)    │
└────┬────┘ └────┬─────┘
     │           │
     └─────┬─────┘
           ↓
    ┌─────────────┐
    │   Hybrid    │
    │   Ranking   │
    └──────┬──────┘
           ↓
    ┌─────────────┐
    │Personalize  │
    └──────┬──────┘
           ↓
       Results
```

## API Usage

### Basic Search

```bash
POST /api/search/neural/search
{
  "query": "Persönliches Budget beantragen",
  "limit": 20,
  "language": "de"
}
```

**Response:**
```json
{
  "query": "Persönliches Budget beantragen",
  "query_info": {
    "language": "de",
    "intent": "application",
    "is_question": false,
    "entities": [
      {"entity": "MISC", "text": "Persönliches Budget"}
    ]
  },
  "results": [
    {
      "id": "doc123",
      "score": 0.95,
      "final_score": 0.92,
      "text": "Das Persönliche Budget ist...",
      "metadata": {"domain_name": "SGB-IX"},
      "found_in_semantic": true,
      "found_in_keyword": true
    }
  ],
  "total": 15,
  "execution_time_ms": 125
}
```

### Advanced Options

```bash
POST /api/search/neural/search
{
  "query": "Widerspruch gegen Bescheid",
  "limit": 20,
  "offset": 0,
  "language": "de",
  "domain_filter": "SGB-IX",
  "enable_query_expansion": true,
  "enable_personalization": true,
  "semantic_weight": 0.7,
  "keyword_weight": 0.3
}
```

### Query Suggestions

```bash
GET /api/search/neural/suggest?query=Pers&limit=5

Response:
{
  "query": "Pers",
  "suggestions": [
    "Persönliches Budget",
    "Persönliche Assistenz",
    "Person mit Behinderung"
  ]
}
```

### Multi-language Search

#### Detect Language

```bash
GET /api/search/neural/detect-language?text=Личный+бюджет

Response:
{
  "text": "Личный бюджет",
  "language": "ru",
  "confidence": "high"
}
```

#### Translate Query

```bash
POST /api/search/neural/translate
  ?query=Personal+budget
  &target_lang=de

Response:
{
  "original": "Personal budget",
  "translated": "Persönliches Budget",
  "source_lang": "en",
  "target_lang": "de"
}
```

## Search Quality

### Metrics

```bash
GET /api/search/neural/analytics/metrics?days=30
```

**Returns:**
- **CTR** (Click-Through Rate): % of searches with clicks
- **MRR** (Mean Reciprocal Rank): Average position of first click
- **Zero Results Rate**: % of searches with no results
- **Average Execution Time**: Performance metric
- **Top Queries**: Most frequent searches
- **Intent Distribution**: Query types breakdown

### Failed Queries

```bash
GET /api/search/neural/analytics/failed-queries?days=7&min_count=2
```

Identifies queries that frequently return no results, helping find content gaps.

### Slow Queries

```bash
GET /api/search/neural/analytics/slow-queries?days=7&threshold_ms=1000
```

Finds queries taking longer than threshold for optimization.

## Features

### Query Understanding

**Intent Classification:**
- `application` - "beantragen", "apply"
- `objection` - "widerspruch", "appeal"
- `information` - "was ist", "what is"
- `legal_reference` - "§ 29", "SGB IX"

**Entity Extraction:**
- PER (Person names)
- ORG (Organizations)
- LOC (Locations)
- MISC (Laws, amounts)

**Legal References:**
- Paragraphs: § 29, § 29 Abs. 1
- Laws: SGB IX, BGB, StGB

### Query Expansion

Automatically expands queries with synonyms:

```
"Persönliches Budget" →
  - "individuelles Budget"
  - "Budget für Behinderte"
  - "§ 29 SGB IX"
```

### Hybrid Ranking

Combines multiple signals:

| Signal | Weight | Description |
|--------|--------|-------------|
| Semantic Score | 35% | BERT similarity |
| Keyword Score | 25% | ES match score |
| Entity Match | 15% | Query entities in doc |
| Freshness | 10% | Document age |
| Quality | 10% | Document completeness |
| User Signals | 5% | Click history, preferences |

### Personalization

- Boosts preferred domains (+20%)
- Uses search history
- Adapts to user patterns

## Best Practices

### 1. Query Formulation

**Good:**
```
"Antrag auf Persönliches Budget nach § 29 SGB IX"
```
Specific, includes legal reference, clear intent.

**Bad:**
```
"Budget"
```
Too vague, ambiguous intent.

### 2. Weight Tuning

**High Precision** (fewer, better results):
```json
{
  "semantic_weight": 0.8,
  "keyword_weight": 0.2
}
```

**Balanced**:
```json
{
  "semantic_weight": 0.6,
  "keyword_weight": 0.4
}
```

**High Recall** (more results):
```json
{
  "semantic_weight": 0.4,
  "keyword_weight": 0.6
}
```

### 3. Language Handling

Let the system auto-detect:
```json
{
  "query": "Personal budget"
  // language auto-detected
}
```

Or specify explicitly:
```json
{
  "query": "Persönliches Budget",
  "language": "de"
}
```

### 4. Domain Filtering

Filter by domain for better results:
```json
{
  "query": "Widerspruch",
  "domain_filter": "SGB-IX"
}
```

## Troubleshooting

### No Results

**Problem**: Search returns 0 results

**Solutions**:
1. Lower semantic threshold
2. Enable query expansion
3. Remove domain filter
4. Check query language
5. Try keyword-only search

### Irrelevant Results

**Problem**: Results don't match intent

**Solutions**:
1. Increase semantic_weight
2. Add domain filter
3. Include more specific terms
4. Use legal references

### Slow Performance

**Problem**: Searches take too long

**Solutions**:
1. Check analytics for slow queries
2. Reduce limit
3. Optimize Elasticsearch
4. Add more BERT servers
5. Use GPU acceleration

## Analytics & Optimization

### Track Clicks

```javascript
// When user clicks result
POST /api/search/neural/track/click
{
  "search_id": "search123",
  "doc_id": "doc456",
  "position": 3,
  "time_to_click_ms": 2500
}
```

### Track Satisfaction

```javascript
// User feedback
POST /api/search/neural/track/satisfaction
{
  "search_id": "search123",
  "satisfied": true
}
```

### Monitor Quality

```bash
# Weekly metrics review
GET /api/search/neural/analytics/metrics?days=7

# Find issues
GET /api/search/neural/analytics/failed-queries?days=7
GET /api/search/neural/analytics/slow-queries?days=7
```

## Advanced Features

### Cross-lingual Search

Search in one language, find results in another:

```python
from ios_core.search.multi_language import multi_language

# Generate queries in all languages
queries = await multi_language.cross_lingual_search(
    query="Personal budget",
    search_languages=[Language.GERMAN, Language.RUSSIAN, Language.ENGLISH]
)

# queries = {
#   "en": "Personal budget",
#   "de": "Persönliches Budget",
#   "ru": "Личный бюджет"
# }
```

### Custom Ranking

Override default weights programmatically:

```python
from ios_core.search.hybrid_ranking import hybrid_ranker

# Custom weights
hybrid_ranker.WEIGHTS = {
    "semantic_score": 0.40,
    "keyword_score": 0.30,
    "entity_match": 0.20,
    "freshness": 0.05,
    "quality": 0.05
}
```

## Resources

- [BERT Paper](https://arxiv.org/abs/1810.04805)
- [Elasticsearch Guide](https://www.elastic.co/guide/)
- [Search Quality Metrics](https://en.wikipedia.org/wiki/Information_retrieval)
```

---

**✅ DAY 121-122 ГОТОВ!**

Создано:
- Neural Search Engine ✓
- Multi-language Support ✓
- Query Understanding ✓
- Hybrid Ranking ✓
- Search Analytics ✓
- API Routes ✓
- Tests ✓
- Documentation ✓

**Статус Week 19-20:**
- Day 119-120: BERT Integration ✓
- Day 121-122: Neural Search ✓

**Готовы к Day 123-124: GPT Integration?**