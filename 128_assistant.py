Пользователь готов продолжить с Search Analytics. Создам подробный раздел о аналитике поиска, метриках, A/B тестировании и оптимизации.

Структура:
1. Search Analytics Architecture
2. Metrics Collection & Tracking
3. Query Analytics
4. Result Quality Metrics
5. A/B Testing Framework
6. Search Suggestions & Autocomplete
7. Performance Monitoring
8. Optimization Recommendations# 🎯 DEEP-DIVE: SEARCH SYSTEM (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 5: `docs/deep-dive/search/SEARCH_ANALYTICS.md`

```markdown
# Search Analytics & Metrics - Deep Dive

## 📊 Analytics Architecture

### Data Collection Pipeline

```
User Search Event
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
  [Query Log]   [Click Log]   [Session Log]  [A/B Test]
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                      │
                      ▼
           ┌─────────────────────┐
           │   Kafka Stream      │
           │   (Real-time)       │
           └──────────┬──────────┘
                      │
       ┌──────────────┼──────────────┐
       │              │              │
       ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│ PostgreSQL │ │   Redis    │ │ ClickHouse │
│ (Hot data) │ │  (Cache)   │ │  (OLAP)    │
└─────┬──────┘ └────────────┘ └─────┬──────┘
      │                             │
      └──────────────┬──────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Analytics Engine   │
          │   • Metrics calc     │
          │   • Aggregations     │
          │   • ML features      │
          └──────────┬───────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
  [Dashboard]  [Reports]    [Alerts]
   Grafana      Email       PagerDuty
```

---

## 🔍 Event Tracking Implementation

### Core Analytics Models

```python
# ios_core/analytics/models.py

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth import get_user_model

User = get_user_model()

class SearchQuery(models.Model):
    """
    Track all search queries
    
    Used for:
    - Popular query analysis
    - Query reformulation tracking
    - Search quality metrics
    - A/B test analysis
    """
    id = models.BigAutoField(primary_key=True)
    
    # Query details
    query_text = models.TextField(db_index=True)
    query_hash = models.CharField(max_length=32, db_index=True)  # MD5 hash
    normalized_query = models.TextField()
    
    # User context
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='search_queries'
    )
    session_id = models.CharField(max_length=64, db_index=True)
    user_agent = models.TextField()
    ip_address = models.GenericIPAddressField()
    
    # Search configuration
    search_mode = models.CharField(
        max_length=20,
        choices=[
            ('keyword', 'Keyword'),
            ('semantic', 'Semantic'),
            ('hybrid', 'Hybrid')
        ]
    )
    filters = JSONField(default=dict)
    page = models.IntegerField(default=1)
    page_size = models.IntegerField(default=10)
    
    # Results metadata
    total_results = models.IntegerField()
    results_shown = models.IntegerField()
    search_time_ms = models.IntegerField()  # Total latency
    
    # Score breakdown
    es_time_ms = models.IntegerField(null=True)
    vector_time_ms = models.IntegerField(null=True)
    fusion_time_ms = models.IntegerField(null=True)
    
    # Cache status
    cache_hit = models.BooleanField(default=False)
    cache_layer = models.CharField(
        max_length=10,
        choices=[('l1', 'L1'), ('l2', 'L2'), ('miss', 'Miss')],
        null=True
    )
    
    # Quality metrics (filled later)
    had_clicks = models.BooleanField(default=False)
    first_click_rank = models.IntegerField(null=True)
    clicks_count = models.IntegerField(default=0)
    
    # A/B testing
    experiment_id = models.CharField(max_length=64, null=True, db_index=True)
    variant = models.CharField(max_length=32, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'analytics_search_query'
        indexes = [
            models.Index(fields=['created_at', 'user']),
            models.Index(fields=['query_hash', 'created_at']),
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['experiment_id', 'variant']),
        ]
    
    def __str__(self):
        return f"{self.query_text} ({self.created_at})"


class SearchClick(models.Model):
    """
    Track clicks on search results
    
    Used for:
    - Click-through rate (CTR)
    - Result relevance signals
    - ML training data
    - Ranking optimization
    """
    id = models.BigAutoField(primary_key=True)
    
    # Link to query
    query = models.ForeignKey(
        SearchQuery,
        on_delete=models.CASCADE,
        related_name='clicks'
    )
    
    # Clicked document
    document_id = models.IntegerField(db_index=True)
    document_title = models.TextField()
    
    # Click position
    rank = models.IntegerField()  # 1-based position in results
    page = models.IntegerField()
    
    # Scores at click time
    final_score = models.FloatField()
    keyword_score = models.FloatField(null=True)
    semantic_score = models.FloatField(null=True)
    
    # Click metadata
    click_timestamp = models.DateTimeField(auto_now_add=True)
    time_to_click_ms = models.IntegerField()  # Time from search to click
    
    # Engagement signals
    dwell_time_seconds = models.IntegerField(null=True)  # Time spent on document
    returned_to_results = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'analytics_search_click'
        indexes = [
            models.Index(fields=['query', 'rank']),
            models.Index(fields=['document_id', 'click_timestamp']),
        ]


class SearchSession(models.Model):
    """
    Track search sessions
    
    Session = sequence of related searches by same user
    
    Used for:
    - Query reformulation analysis
    - Search success measurement
    - User behavior patterns
    """
    id = models.BigAutoField(primary_key=True)
    
    session_id = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Session metadata
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True)
    duration_seconds = models.IntegerField(null=True)
    
    # Session statistics
    queries_count = models.IntegerField(default=0)
    clicks_count = models.IntegerField(default=0)
    reformulations_count = models.IntegerField(default=0)
    
    # Success indicators
    has_successful_search = models.BooleanField(default=False)
    abandonment = models.BooleanField(default=False)  # No clicks at all
    
    class Meta:
        db_table = 'analytics_search_session'
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['start_time', 'end_time']),
        ]


class ZeroResultsQuery(models.Model):
    """
    Track queries with zero results
    
    Critical for search quality improvement
    """
    id = models.BigAutoField(primary_key=True)
    
    query = models.ForeignKey(SearchQuery, on_delete=models.CASCADE)
    query_text = models.TextField(db_index=True)
    
    # Analysis
    possible_reasons = JSONField(default=list)  # ['too_specific', 'typo', 'unsupported_language']
    suggested_queries = JSONField(default=list)
    
    # Resolution
    resolved = models.BooleanField(default=False)
    resolution_action = models.CharField(
        max_length=50,
        choices=[
            ('content_added', 'Content Added'),
            ('synonym_added', 'Synonym Added'),
            ('query_expanded', 'Query Expansion'),
            ('ignored', 'Ignored - Invalid Query')
        ],
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'analytics_zero_results'
        indexes = [
            models.Index(fields=['resolved', 'created_at']),
        ]


class SearchABTest(models.Model):
    """
    Track A/B test experiments
    
    Used for:
    - Testing ranking algorithms
    - Testing UI changes
    - Feature rollout
    """
    id = models.BigAutoField(primary_key=True)
    
    # Experiment details
    experiment_id = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Variants
    variants = JSONField()  # {"control": {...}, "variant_a": {...}}
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('paused', 'Paused'),
            ('completed', 'Completed')
        ],
        default='draft'
    )
    
    # Traffic allocation
    traffic_percentage = models.IntegerField(default=10)  # % of traffic in experiment
    
    # Schedule
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True)
    
    # Results
    sample_size = models.IntegerField(default=0)
    winner = models.CharField(max_length=32, null=True)
    confidence_level = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_ab_test'
```

### Event Tracking Service

```python
# ios_core/analytics/tracking.py

from typing import Dict, List, Optional
import hashlib
import time
from datetime import datetime, timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class SearchAnalytics:
    """
    Central analytics tracking service
    
    Responsibilities:
    - Track search events
    - Calculate metrics
    - Update session data
    - Detect anomalies
    """
    
    def __init__(self):
        self.kafka_producer = None  # Optional: Kafka for real-time streaming
    
    def track_query(
        self,
        query: str,
        user_id: Optional[int],
        session_id: str,
        search_mode: str,
        results_count: int,
        search_time_ms: int,
        request_meta: Dict,
        experiment: Optional[Dict] = None
    ) -> int:
        """
        Track search query event
        
        Returns:
            query_id for linking clicks
        """
        from ios_core.analytics.models import SearchQuery, SearchSession
        
        # Create query record
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        query_record = SearchQuery.objects.create(
            query_text=query,
            query_hash=query_hash,
            normalized_query=query.lower().strip(),
            user_id=user_id,
            session_id=session_id,
            user_agent=request_meta.get('user_agent', ''),
            ip_address=request_meta.get('ip_address', '0.0.0.0'),
            search_mode=search_mode,
            filters=request_meta.get('filters', {}),
            page=request_meta.get('page', 1),
            page_size=request_meta.get('page_size', 10),
            total_results=results_count,
            results_shown=min(results_count, request_meta.get('page_size', 10)),
            search_time_ms=search_time_ms,
            es_time_ms=request_meta.get('es_time_ms'),
            vector_time_ms=request_meta.get('vector_time_ms'),
            fusion_time_ms=request_meta.get('fusion_time_ms'),
            cache_hit=request_meta.get('cache_hit', False),
            cache_layer=request_meta.get('cache_layer'),
            experiment_id=experiment.get('id') if experiment else None,
            variant=experiment.get('variant') if experiment else None
        )
        
        # Update or create session
        session, created = SearchSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                'user_id': user_id,
                'start_time': timezone.now(),
                'queries_count': 1
            }
        )
        
        if not created:
            session.queries_count += 1
            session.end_time = timezone.now()
            session.duration_seconds = int(
                (session.end_time - session.start_time).total_seconds()
            )
            session.save()
        
        # Track zero results
        if results_count == 0:
            self._track_zero_results(query_record)
        
        # Stream to Kafka (optional)
        if self.kafka_producer:
            self._stream_to_kafka('search_query', {
                'query_id': query_record.id,
                'query': query,
                'user_id': user_id,
                'timestamp': query_record.created_at.isoformat(),
                'results_count': results_count,
                'search_time_ms': search_time_ms
            })
        
        logger.info(
            f"Tracked query: '{query}' "
            f"(user={user_id}, results={results_count}, time={search_time_ms}ms)"
        )
        
        return query_record.id
    
    def track_click(
        self,
        query_id: int,
        document_id: int,
        document_title: str,
        rank: int,
        page: int,
        scores: Dict,
        time_to_click_ms: int
    ):
        """Track result click event"""
        from ios_core.analytics.models import SearchClick, SearchQuery
        
        click = SearchClick.objects.create(
            query_id=query_id,
            document_id=document_id,
            document_title=document_title,
            rank=rank,
            page=page,
            final_score=scores.get('final', 0),
            keyword_score=scores.get('keyword'),
            semantic_score=scores.get('semantic'),
            time_to_click_ms=time_to_click_ms
        )
        
        # Update query with click info
        query = SearchQuery.objects.get(id=query_id)
        
        if not query.had_clicks:
            query.had_clicks = True
            query.first_click_rank = rank
        
        query.clicks_count += 1
        query.save()
        
        # Update session
        session = SearchSession.objects.get(session_id=query.session_id)
        session.clicks_count += 1
        session.has_successful_search = True
        session.save()
        
        logger.info(
            f"Tracked click: doc={document_id}, rank={rank}, "
            f"query_id={query_id}"
        )
        
        return click.id
    
    def track_dwell_time(
        self,
        click_id: int,
        dwell_time_seconds: int,
        returned_to_results: bool
    ):
        """Track time spent on clicked document"""
        from ios_core.analytics.models import SearchClick
        
        SearchClick.objects.filter(id=click_id).update(
            dwell_time_seconds=dwell_time_seconds,
            returned_to_results=returned_to_results
        )
        
        # Short dwell time + return = bad result
        if dwell_time_seconds < 10 and returned_to_results:
            logger.warning(f"Potential bad result: click_id={click_id}")
    
    def _track_zero_results(self, query: 'SearchQuery'):
        """Track query with zero results"""
        from ios_core.analytics.models import ZeroResultsQuery
        
        # Analyze possible reasons
        reasons = self._analyze_zero_results(query.query_text)
        
        # Generate suggestions
        suggestions = self._generate_query_suggestions(query.query_text)
        
        ZeroResultsQuery.objects.create(
            query=query,
            query_text=query.query_text,
            possible_reasons=reasons,
            suggested_queries=suggestions
        )
        
        logger.warning(f"Zero results for: '{query.query_text}'")
    
    def _analyze_zero_results(self, query: str) -> List[str]:
        """Analyze why query returned zero results"""
        reasons = []
        
        # Check if query is too specific
        if len(query.split()) > 7:
            reasons.append('too_specific')
        
        # Check for potential typos
        # (In production, use spell checker)
        if any(len(word) > 15 for word in query.split()):
            reasons.append('possible_typo')
        
        # Check if query contains special characters
        if any(c in query for c in ['@', '#', '$', '%']):
            reasons.append('special_characters')
        
        return reasons
    
    def _generate_query_suggestions(self, query: str) -> List[str]:
        """Generate alternative query suggestions"""
        # In production, use:
        # - Edit distance to popular queries
        # - Synonym expansion
        # - Query relaxation
        
        suggestions = []
        
        # Simple: remove last word (query relaxation)
        words = query.split()
        if len(words) > 1:
            suggestions.append(' '.join(words[:-1]))
        
        return suggestions
    
    def _stream_to_kafka(self, topic: str, event: Dict):
        """Stream event to Kafka for real-time processing"""
        if self.kafka_producer:
            try:
                self.kafka_producer.send(topic, value=event)
            except Exception as e:
                logger.error(f"Failed to stream to Kafka: {e}")


# Global instance
_analytics = None

def get_analytics() -> SearchAnalytics:
    """Get global analytics instance"""
    global _analytics
    if _analytics is None:
        _analytics = SearchAnalytics()
    return _analytics
```

### API Integration

```python
# ios_core/api/views/search.py

from rest_framework.decorators import api_view
from rest_framework.response import Response
from ios_core.search import get_hybrid_search_engine
from ios_core.analytics.tracking import get_analytics
import time

@api_view(['POST'])
def search(request):
    """
    Search endpoint with analytics tracking
    """
    # Parse request
    query = request.data.get('query')
    page = request.data.get('page', 1)
    page_size = request.data.get('page_size', 10)
    filters = request.data.get('filters', {})
    
    # Get search engine
    engine = get_hybrid_search_engine()
    
    # Execute search with timing
    start_time = time.time()
    
    results = engine.search(
        query=query,
        page=page,
        page_size=page_size,
        filters=filters,
        user_id=request.user.id if request.user.is_authenticated else None,
        user_context={
            'language': request.LANGUAGE_CODE,
            'user_id': request.user.id if request.user.is_authenticated else None
        }
    )
    
    search_time_ms = int((time.time() - start_time) * 1000)
    
    # Track analytics
    analytics = get_analytics()
    
    query_id = analytics.track_query(
        query=query,
        user_id=request.user.id if request.user.is_authenticated else None,
        session_id=request.session.session_key,
        search_mode='hybrid',
        results_count=len(results),
        search_time_ms=search_time_ms,
        request_meta={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': request.META.get('REMOTE_ADDR', ''),
            'filters': filters,
            'page': page,
            'page_size': page_size
        }
    )
    
    # Format response
    return Response({
        'query_id': query_id,  # For click tracking
        'total_results': len(results),
        'results': [
            {
                'document_id': r.document_id,
                'title': r.title,
                'summary': r.summary,
                'score': r.final_score,
                'rank': r.rank,
                'highlights': r.highlights
            }
            for r in results
        ],
        'search_time_ms': search_time_ms
    })


@api_view(['POST'])
def track_click(request):
    """
    Track click on search result
    """
    analytics = get_analytics()
    
    click_id = analytics.track_click(
        query_id=request.data['query_id'],
        document_id=request.data['document_id'],
        document_title=request.data['document_title'],
        rank=request.data['rank'],
        page=request.data['page'],
        scores=request.data['scores'],
        time_to_click_ms=request.data['time_to_click_ms']
    )
    
    return Response({'click_id': click_id})


@api_view(['POST'])
def track_dwell_time(request):
    """
    Track time spent on document
    """
    analytics = get_analytics()
    
    analytics.track_dwell_time(
        click_id=request.data['click_id'],
        dwell_time_seconds=request.data['dwell_time_seconds'],
        returned_to_results=request.data['returned_to_results']
    )
    
    return Response({'status': 'ok'})
```

---

## 📈 Metrics Calculation

### Key Performance Indicators (KPIs)

```python
# ios_core/analytics/metrics.py

from typing import Dict, List
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q, F
from django.utils import timezone

class SearchMetrics:
    """
    Calculate search quality metrics
    
    Metrics:
    - Click-through rate (CTR)
    - Mean Reciprocal Rank (MRR)
    - Zero results rate
    - Query latency
    - User satisfaction
    """
    
    def calculate_ctr(
        self,
        start_date: datetime,
        end_date: datetime,
        segment: Optional[str] = None
    ) -> Dict:
        """
        Calculate Click-Through Rate
        
        CTR = (Queries with clicks) / (Total queries)
        
        Higher is better (target: >30%)
        """
        from ios_core.analytics.models import SearchQuery
        
        # Base query
        queries = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        )
        
        # Apply segmentation
        if segment == 'mobile':
            queries = queries.filter(user_agent__icontains='Mobile')
        elif segment == 'desktop':
            queries = queries.exclude(user_agent__icontains='Mobile')
        
        # Calculate
        total_queries = queries.count()
        queries_with_clicks = queries.filter(had_clicks=True).count()
        
        ctr = queries_with_clicks / total_queries if total_queries > 0 else 0
        
        # CTR by position
        ctr_by_position = {}
        for rank in range(1, 11):
            clicks_at_rank = SearchClick.objects.filter(
                query__created_at__gte=start_date,
                query__created_at__lt=end_date,
                rank=rank
            ).count()
            
            ctr_by_position[rank] = clicks_at_rank / total_queries if total_queries > 0 else 0
        
        return {
            'overall_ctr': ctr,
            'total_queries': total_queries,
            'queries_with_clicks': queries_with_clicks,
            'ctr_by_position': ctr_by_position
        }
    
    def calculate_mrr(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """
        Calculate Mean Reciprocal Rank
        
        MRR = Average(1 / rank_of_first_click)
        
        Measures how high the first clicked result ranks
        Higher is better (target: >0.7)
        """
        from ios_core.analytics.models import SearchQuery
        
        # Get queries with clicks
        queries_with_clicks = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            had_clicks=True,
            first_click_rank__isnull=False
        )
        
        if queries_with_clicks.count() == 0:
            return 0.0
        
        # Calculate reciprocal ranks
        reciprocal_ranks = [
            1.0 / q.first_click_rank
            for q in queries_with_clicks
        ]
        
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        
        return mrr
    
    def calculate_zero_results_rate(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate Zero Results Rate
        
        ZRR = (Queries with 0 results) / (Total queries)
        
        Lower is better (target: <5%)
        """
        from ios_core.analytics.models import SearchQuery
        
        total_queries = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).count()
        
        zero_results = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            total_results=0
        ).count()
        
        zrr = zero_results / total_queries if total_queries > 0 else 0
        
        # Top zero-result queries
        top_zero_queries = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            total_results=0
        ).values('query_text').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return {
            'zero_results_rate': zrr,
            'zero_results_count': zero_results,
            'total_queries': total_queries,
            'top_zero_queries': list(top_zero_queries)
        }
    
    def calculate_latency_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate search latency metrics
        
        Metrics:
        - P50, P95, P99 latency
        - Average latency
        - Cache hit rate impact
        """
        from ios_core.analytics.models import SearchQuery
        import numpy as np
        
        # Get all search times
        search_times = list(
            SearchQuery.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date
            ).values_list('search_time_ms', flat=True)
        )
        
        if not search_times:
            return {}
        
        # Calculate percentiles
        p50 = np.percentile(search_times, 50)
        p95 = np.percentile(search_times, 95)
        p99 = np.percentile(search_times, 99)
        avg = np.mean(search_times)
        
        # Cache hit impact
        cache_hit_times = list(
            SearchQuery.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                cache_hit=True
            ).values_list('search_time_ms', flat=True)
        )
        
        cache_miss_times = list(
            SearchQuery.objects.filter(
                created_at__gte=start_date,
                created_at__lt=end_date,
                cache_hit=False
            ).values_list('search_time_ms', flat=True)
        )
        
        return {
            'p50_ms': p50,
            'p95_ms': p95,
            'p99_ms': p99,
            'avg_ms': avg,
            'cache_hit_avg_ms': np.mean(cache_hit_times) if cache_hit_times else 0,
            'cache_miss_avg_ms': np.mean(cache_miss_times) if cache_miss_times else 0,
            'total_queries': len(search_times)
        }
    
    def calculate_session_metrics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate session-based metrics
        
        Metrics:
        - Average queries per session
        - Average session duration
        - Session success rate
        - Abandonment rate
        """
        from ios_core.analytics.models import SearchSession
        
        sessions = SearchSession.objects.filter(
            start_time__gte=start_date,
            start_time__lt=end_date
        )
        
        total_sessions = sessions.count()
        
        if total_sessions == 0:
            return {}
        
        # Aggregations
        stats = sessions.aggregate(
            avg_queries=Avg('queries_count'),
            avg_duration=Avg('duration_seconds'),
            successful_sessions=Count('id', filter=Q(has_successful_search=True)),
            abandoned_sessions=Count('id', filter=Q(abandonment=True))
        )
        
        return {
            'avg_queries_per_session': stats['avg_queries'],
            'avg_session_duration_seconds': stats['avg_duration'],
            'session_success_rate': stats['successful_sessions'] / total_sessions,
            'abandonment_rate': stats['abandoned_sessions'] / total_sessions,
            'total_sessions': total_sessions
        }
    
    def get_popular_queries(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 20
    ) -> List[Dict]:
        """Get most popular search queries"""
        from ios_core.analytics.models import SearchQuery
        
        popular = SearchQuery.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date
        ).values('query_text').annotate(
            search_count=Count('id'),
            avg_results=Avg('total_results'),
            ctr=Avg('had_clicks', output_field=models.FloatField())
        ).order_by('-search_count')[:limit]
        
        return list(popular)
    
    def get_trending_queries(
        self,
        current_period_days: int = 7,
        previous_period_days: int = 7
    ) -> List[Dict]:
        """
        Get trending queries
        
        Queries with significant increase in search volume
        """
        from ios_core.analytics.models import SearchQuery
        
        now = timezone.now()
        current_start = now - timedelta(days=current_period_days)
        previous_start = now - timedelta(days=current_period_days + previous_period_days)
        previous_end = current_start
        
        # Current period counts
        current_counts = dict(
            SearchQuery.objects.filter(
                created_at__gte=current_start
            ).values('query_text').annotate(
                count=Count('id')
            ).values_list('query_text', 'count')
        )
        
        # Previous period counts
        previous_counts = dict(
            SearchQuery.objects.filter(
                created_at__gte=previous_start,
                created_at__lt=previous_end
            ).values('query_text').annotate(
                count=Count('id')
            ).values_list('query_text', 'count')
        )
        
        # Calculate trends
        trends = []
        for query, current_count in current_counts.items():
            previous_count = previous_counts.get(query, 0)
            
            # Avoid division by zero
            if previous_count == 0:
                growth_rate = float('inf') if current_count > 0 else 0
            else:
                growth_rate = (current_count - previous_count) / previous_count
            
            # Only include significant increases
            if growth_rate > 0.5 and current_count > 5:
                trends.append({
                    'query': query,
                    'current_count': current_count,
                    'previous_count': previous_count,
                    'growth_rate': growth_rate
                })
        
        # Sort by growth rate
        trends.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        return trends[:20]


# Example usage
def generate_daily_report():
    """Generate daily search metrics report"""
    metrics = SearchMetrics()
    
    # Yesterday's data
    end_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = end_date - timedelta(days=1)
    
    # Calculate all metrics
    ctr = metrics.calculate_ctr(start_date, end_date)
    mrr = metrics.calculate_mrr(start_date, end_date)
    zrr = metrics.calculate_zero_results_rate(start_date, end_date)
    latency = metrics.calculate_latency_metrics(start_date, end_date)
    sessions = metrics.calculate_session_metrics(start_date, end_date)
    popular = metrics.get_popular_queries(start_date, end_date, limit=10)
    trending = metrics.get_trending_queries()
    
    report = {
        'date': start_date.strftime('%Y-%m-%d'),
        'ctr': ctr,
        'mrr': mrr,
        'zero_results': zrr,
        'latency': latency,
        'sessions': sessions,
        'popular_queries': popular,
        'trending_queries': trending
    }
    
    return report
```

---

## 📊 Dashboard & Visualization

### Grafana Dashboard Configuration

```yaml
# grafana/dashboards/search_analytics.json

{
  "dashboard": {
    "title": "Search Analytics",
    "tags": ["search", "analytics"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Search Volume (24h)",
        "type": "graph",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                date_trunc('hour', created_at) as time,
                COUNT(*) as queries
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
              GROUP BY time
              ORDER BY time
            "
          }
        ]
      },
      {
        "title": "Click-Through Rate",
        "type": "stat",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                ROUND(
                  COUNT(*) FILTER (WHERE had_clicks = true)::numeric /
                  COUNT(*)::numeric * 100,
                  2
                ) as ctr
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
            "
          }
        ],
        "options": {
          "unit": "percent",
          "colorMode": "value",
          "graphMode": "area",
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {"value": 0, "color": "red"},
              {"value": 20, "color": "yellow"},
              {"value": 30, "color": "green"}
            ]
          }
        }
      },
      {
        "title": "Search Latency (P95)",
        "type": "graph",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                date_trunc('hour', created_at) as time,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY search_time_ms) as p95
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
              GROUP BY time
              ORDER BY time
            "
          }
        ],
        "yaxes": [
          {"format": "ms", "label": "Latency"}
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {"params": [200], "type": "gt"},
              "operator": {"type": "and"},
              "query": {"params": ["A", "5m", "now"]},
              "reducer": {"params": [], "type": "avg"},
              "type": "query"
            }
          ],
          "name": "High Search Latency",
          "message": "P95 latency exceeded 200ms"
        }
      },
      {
        "title": "Zero Results Rate",
        "type": "stat",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                ROUND(
                  COUNT(*) FILTER (WHERE total_results = 0)::numeric /
                  COUNT(*)::numeric * 100,
                  2
                ) as zrr
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
            "
          }
        ],
        "options": {
          "unit": "percent",
          "thresholds": {
            "steps": [
              {"value": 0, "color": "green"},
              {"value": 5, "color": "yellow"},
              {"value": 10, "color": "red"}
            ]
          }
        }
      },
      {
        "title": "Top Queries (24h)",
        "type": "table",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                query_text as \"Query\",
                COUNT(*) as \"Count\",
                ROUND(AVG(total_results), 0) as \"Avg Results\",
                ROUND(AVG(had_clicks::int) * 100, 1) as \"CTR %\"
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
              GROUP BY query_text
              ORDER BY COUNT(*) DESC
              LIMIT 20
            "
          }
        ]
      },
      {
        "title": "Search Mode Distribution",
        "type": "piechart",
        "datasource": "PostgreSQL",
        "targets": [
          {
            "rawSql": "
              SELECT
                search_mode as metric,
                COUNT(*) as value
              FROM analytics_search_query
              WHERE created_at > NOW() - INTERVAL '24 hours'
              GROUP BY search_mode
            "
          }
        ]
      }
    ]
  }
}
```

---

**Продолжение следует...**

Создано:
- ✅ Complete analytics data models
- ✅ Event tracking system
- ✅ Metrics calculation (CTR, MRR, ZRR, latency)
- ✅ Session analytics
- ✅ Grafana dashboard configuration

**Следующие разделы:**
1. A/B Testing Framework
2. Query Suggestions & Autocomplete
3. Performance Monitoring & Alerts
4. Optimization Recommendations

**Готовы продолжить с A/B Testing?**