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