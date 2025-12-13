Пользователь хочет продолжить с Sprint 5-6, который посвящен API Endpoints и Caching. Это критически важная часть, где мы создаем RESTful API и добавляем кэширование Redis для оптимизации производительности.

Нужно создать:
1. API Views (DRF)
2. Serializers
3. URL routing
4. Caching layer
5. Rate limiting
6. API documentation (Swagger)
7. Tests для API

Продолжу в том же формате с подробными примерами кода.## ФАЙЛ 19 (продолжение): API Endpoints & Caching Layer

```markdown
# Phase Implementation Details (продолжение)

### Sprint 5-6: API & Caching (Weeks 6-7)

#### Task 5.1: API Serializers
**Assignee:** Backend Developer
**Time:** 1 day
**Priority:** Critical

```python
# search/serializers.py

"""
DRF Serializers for search API
"""

from rest_framework import serializers
from .models import Document, SearchQuery, UserPreference, ClickEvent
from django.contrib.auth.models import User

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'summary',
            'document_type',
            'category',
            'legal_code',
            'paragraph',
            'tags',
            'created_at',
            'updated_at',
            'published_at',
            'view_count',
            'click_count',
            'is_active'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'view_count',
            'click_count'
        ]

class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Document with full content"""
    
    class Meta:
        model = Document
        fields = [
            'id',
            'title',
            'content',
            'summary',
            'document_type',
            'category',
            'legal_code',
            'paragraph',
            'tags',
            'source_url',
            'source_name',
            'author',
            'version',
            'effective_date',
            'created_at',
            'updated_at',
            'published_at',
            'view_count',
            'click_count',
            'is_active',
            'is_public'
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'view_count',
            'click_count'
        ]

class SearchRequestSerializer(serializers.Serializer):
    """Serializer for search request"""
    
    query = serializers.CharField(
        required=True,
        max_length=500,
        help_text='Search query'
    )
    
    filters = serializers.DictField(
        required=False,
        default=dict,
        help_text='Search filters'
    )
    
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text='Page number'
    )
    
    page_size = serializers.IntegerField(
        required=False,
        default=20,
        min_value=1,
        max_value=100,
        help_text='Results per page'
    )
    
    sort_by = serializers.ChoiceField(
        required=False,
        default='relevance',
        choices=[
            'relevance',
            'date_desc',
            'date_asc',
            'title',
            'popularity'
        ],
        help_text='Sort option'
    )
    
    def validate_filters(self, value):
        """Validate filters structure"""
        allowed_filters = [
            'document_type',
            'category',
            'legal_code',
            'tags',
            'date_from',
            'date_to'
        ]
        
        for key in value.keys():
            if key not in allowed_filters:
                raise serializers.ValidationError(
                    f"Invalid filter: {key}. Allowed: {allowed_filters}"
                )
        
        return value

class SearchResultSerializer(serializers.Serializer):
    """Serializer for individual search result"""
    
    id = serializers.UUIDField()
    score = serializers.FloatField()
    rank = serializers.IntegerField()
    source = serializers.CharField()
    title = serializers.CharField()
    summary = serializers.CharField(required=False, allow_blank=True)
    document_type = serializers.CharField()
    category = serializers.CharField()
    legal_code = serializers.CharField(required=False, allow_blank=True)
    paragraph = serializers.CharField(required=False, allow_blank=True)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    created_at = serializers.DateTimeField()
    view_count = serializers.IntegerField(required=False)
    click_count = serializers.IntegerField(required=False)

class SearchResponseSerializer(serializers.Serializer):
    """Serializer for search response"""
    
    results = SearchResultSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    search_time_ms = serializers.IntegerField()
    fusion_algorithm = serializers.CharField(required=False)
    query = serializers.CharField()
    filters = serializers.DictField()

class AutocompleteRequestSerializer(serializers.Serializer):
    """Serializer for autocomplete request"""
    
    query = serializers.CharField(
        required=True,
        max_length=100,
        min_length=1,
        help_text='Autocomplete prefix'
    )
    
    limit = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=20,
        help_text='Maximum suggestions'
    )

class AutocompleteSuggestionSerializer(serializers.Serializer):
    """Serializer for autocomplete suggestion"""
    
    text = serializers.CharField()
    score = serializers.FloatField()
    frequency = serializers.IntegerField(required=False)

class ClickEventSerializer(serializers.ModelSerializer):
    """Serializer for click event tracking"""
    
    class Meta:
        model = ClickEvent
        fields = [
            'id',
            'search_query',
            'document',
            'position',
            'score',
            'dwell_time_seconds',
            'clicked_at'
        ]
        read_only_fields = ['id', 'clicked_at']

class ClickTrackingSerializer(serializers.Serializer):
    """Serializer for click tracking request"""
    
    query_id = serializers.UUIDField(
        required=True,
        help_text='Search query ID'
    )
    
    document_id = serializers.UUIDField(
        required=True,
        help_text='Clicked document ID'
    )
    
    position = serializers.IntegerField(
        required=True,
        min_value=1,
        help_text='Position in results (1-based)'
    )
    
    score = serializers.FloatField(
        required=False,
        help_text='Search score'
    )

class UserPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for user preferences"""
    
    class Meta:
        model = UserPreference
        fields = [
            'preferred_document_types',
            'preferred_categories',
            'language_preference',
            'default_page_size',
            'default_sort',
            'search_history'
        ]

class FacetsSerializer(serializers.Serializer):
    """Serializer for faceted search results"""
    
    field = serializers.CharField()
    values = serializers.ListField(
        child=serializers.DictField()
    )

class SearchStatsSerializer(serializers.Serializer):
    """Serializer for search statistics"""
    
    total_searches = serializers.IntegerField()
    unique_queries = serializers.IntegerField()
    avg_search_time_ms = serializers.FloatField()
    top_queries = serializers.ListField(
        child=serializers.DictField()
    )
    searches_by_day = serializers.ListField(
        child=serializers.DictField()
    )
```

---

#### Task 5.2: API Views
**Assignee:** Backend Developer
**Time:** 3 days
**Priority:** Critical

```python
# search/views.py

"""
API Views for search functionality
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Document, SearchQuery, ClickEvent
from .serializers import (
    SearchRequestSerializer,
    SearchResponseSerializer,
    DocumentSerializer,
    DocumentDetailSerializer,
    AutocompleteRequestSerializer,
    AutocompleteSuggestionSerializer,
    ClickTrackingSerializer,
    UserPreferenceSerializer,
    SearchStatsSerializer
)
from .services.hybrid_search import HybridSearchService
from .services.caching import CacheService

import logging
import hashlib
import json

logger = logging.getLogger(__name__)

class SearchView(viewsets.ViewSet):
    """
    ViewSet for search operations
    """
    
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_service = HybridSearchService()
        self.cache_service = CacheService()
    
    @swagger_auto_schema(
        operation_description="Search documents using hybrid search",
        request_body=SearchRequestSerializer,
        responses={
            200: SearchResponseSerializer,
            400: "Bad request",
            500: "Internal server error"
        },
        tags=['Search']
    )
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        Perform hybrid search
        
        Combines Elasticsearch full-text search with Qdrant vector search
        """
        import time
        start_time = time.time()
        
        # Validate request
        serializer = SearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        query = validated_data['query']
        filters = validated_data.get('filters', {})
        page = validated_data.get('page', 1)
        page_size = validated_data.get('page_size', 20)
        sort_by = validated_data.get('sort_by', 'relevance')
        
        # Generate cache key
        cache_key = self.cache_service.generate_search_cache_key(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
            sort_by=sort_by
        )
        
        # Try cache first
        cached_result = self.cache_service.get_search_results(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {query}")
            return Response(cached_result, status=status.HTTP_200_OK)
        
        # Perform search
        try:
            results = self.search_service.search(
                query=query,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by
            )
            
            # Track search query
            search_query = self._track_search_query(
                request=request,
                query=query,
                filters=filters,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                total_results=results['total'],
                search_time_ms=results['search_time_ms']
            )
            
            # Add query ID to response
            results['query_id'] = str(search_query.id)
            results['query'] = query
            results['filters'] = filters
            
            # Cache results
            self.cache_service.set_search_results(cache_key, results)
            
            logger.info(
                f"Search completed: query='{query}', "
                f"results={results['total']}, "
                f"time={results['search_time_ms']}ms"
            )
            
            return Response(results, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Search error: {e}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @swagger_auto_schema(
        operation_description="Get autocomplete suggestions",
        query_serializer=AutocompleteRequestSerializer,
        responses={
            200: AutocompleteSuggestionSerializer(many=True),
            400: "Bad request"
        },
        tags=['Search']
    )
    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        """
        Get autocomplete suggestions
        """
        serializer = AutocompleteRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        query = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 10)
        
        # Check cache
        cache_key = f"autocomplete:{query.lower()}"
        cached = cache.get(cache_key)
        
        if cached:
            return Response(cached[:limit], status=status.HTTP_200_OK)
        
        # Get suggestions (implement autocomplete service)
        # For now, return simple prefix matching
        from django.db.models import Q, Count
        
        suggestions = SearchQuery.objects.filter(
            query_text__istartswith=query
        ).values('query_text').annotate(
            frequency=Count('id')
        ).order_by('-frequency')[:limit]
        
        result = [
            {
                'text': s['query_text'],
                'frequency': s['frequency'],
                'score': 1.0
            }
            for s in suggestions
        ]
        
        # Cache for 5 minutes
        cache.set(cache_key, result, 300)
        
        return Response(result, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Track click on search result",
        request_body=ClickTrackingSerializer,
        responses={
            201: "Click tracked successfully",
            400: "Bad request",
            404: "Query or document not found"
        },
        tags=['Analytics']
    )
    @action(detail=False, methods=['post'])
    def track_click(self, request):
        """
        Track click event on search result
        """
        serializer = ClickTrackingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        
        try:
            # Get search query
            search_query = SearchQuery.objects.get(
                id=validated_data['query_id']
            )
            
            # Get document
            document = Document.objects.get(
                id=validated_data['document_id']
            )
            
            # Create click event
            click_event = ClickEvent.objects.create(
                search_query=search_query,
                document=document,
                position=validated_data['position'],
                score=validated_data.get('score')
            )
            
            # Update document click count
            document.increment_click_count()
            
            # Add to search query clicked results
            search_query.add_clicked_result(
                document_id=str(document.id),
                position=validated_data['position']
            )
            
            logger.info(
                f"Click tracked: query={search_query.query_text}, "
                f"doc={document.id}, position={validated_data['position']}"
            )
            
            return Response(
                {'status': 'Click tracked'},
                status=status.HTTP_201_CREATED
            )
        
        except SearchQuery.DoesNotExist:
            return Response(
                {'error': 'Search query not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error tracking click: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to track click'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _track_search_query(
        self,
        request,
        query: str,
        filters: dict,
        page: int,
        page_size: int,
        sort_by: str,
        total_results: int,
        search_time_ms: int
    ) -> SearchQuery:
        """Track search query in database"""
        
        # Get user info
        user = request.user if request.user.is_authenticated else None
        session_id = request.session.session_key or 'anonymous'
        
        # Get IP and user agent
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Normalize query
        query_normalized = query.lower().strip()
        
        # Create search query record
        search_query = SearchQuery.objects.create(
            query_text=query,
            query_normalized=query_normalized,
            user=user,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            filters=filters,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
            total_results=total_results,
            results_returned=min(page_size, total_results),
            search_time_ms=search_time_ms,
            search_type='hybrid'
        )
        
        return search_query
    
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for document operations
    """
    
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    queryset = Document.objects.filter(is_active=True, is_public=True)
    serializer_class = DocumentSerializer
    
    def get_serializer_class(self):
        """Use detailed serializer for retrieve action"""
        if self.action == 'retrieve':
            return DocumentDetailSerializer
        return DocumentSerializer
    
    @swagger_auto_schema(
        operation_description="Get document by ID",
        responses={
            200: DocumentDetailSerializer,
            404: "Document not found"
        },
        tags=['Documents']
    )
    def retrieve(self, request, pk=None):
        """
        Get document details
        
        Increments view count
        """
        try:
            document = self.get_object()
            
            # Increment view count
            document.increment_view_count()
            
            serializer = self.get_serializer(document)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @swagger_auto_schema(
        operation_description="Get similar documents",
        responses={
            200: DocumentSerializer(many=True),
            404: "Document not found"
        },
        tags=['Documents']
    )
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """
        Find similar documents using vector search
        """
        try:
            document = self.get_object()
            
            # Use Qdrant to find similar documents
            from .services.qdrant_service import QdrantService
            qdrant_service = QdrantService()
            
            # Get document's embedding and search
            # (Simplified - in reality, you'd store the embedding)
            text = f"{document.title} {document.summary or document.content[:500]}"
            
            similar = qdrant_service.search(
                query=text,
                limit=10
            )
            
            # Filter out the original document
            similar_ids = [
                s['id'] for s in similar
                if s['id'] != str(document.id)
            ][:5]
            
            # Get documents
            documents = Document.objects.filter(
                id__in=similar_ids,
                is_active=True,
                is_public=True
            )
            
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Document.DoesNotExist:
            return Response(
                {'error': 'Document not found'},
                status=status.HTTP_404_NOT_FOUND
            )

@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint",
    responses={200: "OK"},
    tags=['System']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    System health check
    
    Checks:
    - Database connection
    - Elasticsearch connection
    - Qdrant connection
    - Redis connection
    """
    health = {
        'status': 'healthy',
        'services': {}
    }
    
    # Check database
    try:
        from django.db import connection
        connection.ensure_connection()
        health['services']['database'] = 'up'
    except Exception as e:
        health['services']['database'] = 'down'
        health['status'] = 'degraded'
        logger.error(f"Database health check failed: {e}")
    
    # Check Elasticsearch
    try:
        from .services.elasticsearch_service import ElasticsearchService
        es = ElasticsearchService()
        es.client.cluster.health()
        health['services']['elasticsearch'] = 'up'
    except Exception as e:
        health['services']['elasticsearch'] = 'down'
        health['status'] = 'degraded'
        logger.error(f"Elasticsearch health check failed: {e}")
    
    # Check Qdrant
    try:
        from .services.qdrant_service import QdrantService
        qdrant = QdrantService()
        qdrant.client.get_collections()
        health['services']['qdrant'] = 'up'
    except Exception as e:
        health['services']['qdrant'] = 'down'
        health['status'] = 'degraded'
        logger.error(f"Qdrant health check failed: {e}")
    
    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        health['services']['redis'] = 'up'
    except Exception as e:
        health['services']['redis'] = 'down'
        health['status'] = 'degraded'
        logger.error(f"Redis health check failed: {e}")
    
    status_code = status.HTTP_200_OK if health['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return Response(health, status=status_code)
```

---

#### Task 5.3: Caching Service
**Assignee:** Backend Developer
**Time:** 2 days
**Priority:** High

```python
# search/services/caching.py

"""
Caching service for search results
"""

from django.core.cache import cache
from django.conf import settings
import hashlib
import json
import logging
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

class CacheService:
    """
    Multi-layer caching service
    
    Layers:
    1. Query results cache (5 minutes)
    2. Popular queries cache (1 hour)
    3. Document details cache (30 minutes)
    4. Autocomplete cache (10 minutes)
    """
    
    # Cache TTLs (seconds)
    TTL_SEARCH_RESULTS = 300      # 5 minutes
    TTL_POPULAR_QUERIES = 3600    # 1 hour
    TTL_DOCUMENT = 1800           # 30 minutes
    TTL_AUTOCOMPLETE = 600        # 10 minutes
    TTL_AGGREGATIONS = 1800       # 30 minutes
    
    # Cache key prefixes
    PREFIX_SEARCH = 'search'
    PREFIX_DOCUMENT = 'doc'
    PREFIX_AUTOCOMPLETE = 'ac'
    PREFIX_POPULAR = 'popular'
    PREFIX_AGGREGATIONS = 'agg'
    
    def generate_search_cache_key(
        self,
        query: str,
        filters: Dict,
        page: int,
        page_size: int,
        sort_by: str
    ) -> str:
        """
        Generate cache key for search results
        
        Args:
            query: Search query
            filters: Search filters
            page: Page number
            page_size: Results per page
            sort_by: Sort option
        
        Returns:
            Cache key
        """
        # Create deterministic string
        key_data = {
            'query': query.lower().strip(),
            'filters': filters,
            'page': page,
            'page_size': page_size,
            'sort_by': sort_by
        }
        
        # Sort for consistency
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Hash for shorter key
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.PREFIX_SEARCH}:{key_hash}"
    
    def get_search_results(self, cache_key: str) -> Optional[Dict]:
        """
        Get cached search results
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached results or None
        """
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached
            logger.debug(f"Cache miss: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set_search_results(
        self,
        cache_key: str,
        results: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache search results
        
        Args:
            cache_key: Cache key
            results: Search results
            ttl: Time to live (optional)
        
        Returns:
            Success status
        """
        try:
            ttl = ttl or self.TTL_SEARCH_RESULTS
            cache.set(cache_key, results, ttl)
            logger.debug(f"Cached results: {cache_key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get cached document"""
        cache_key = f"{self.PREFIX_DOCUMENT}:{document_id}"
        return cache.get(cache_key)
    
    def set_document(
        self,
        document_id: str,
        document_data: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache document"""
        try:
            cache_key = f"{self.PREFIX_DOCUMENT}:{document_id}"
            ttl = ttl or self.TTL_DOCUMENT
            cache.set(cache_key, document_data, ttl)
            return True
        except Exception as e:
            logger.error(f"Error caching document: {e}")
            return False
    
    def invalidate_document(self, document_id: str):
        """Invalidate document cache"""
        cache_key = f"{self.PREFIX_DOCUMENT}:{document_id}"
        cache.delete(cache_key)
        logger.debug(f"Invalidated cache: {cache_key}")
    
    def get_autocomplete_suggestions(
        self,
        prefix: str
    ) -> Optional[List[Dict]]:
        """Get cached autocomplete suggestions"""
        cache_key = f"{self.PREFIX_AUTOCOMPLETE}:{prefix.lower()}"
        return cache.get(cache_key)
    
    def set_autocomplete_suggestions(
        self,
        prefix: str,
        suggestions: List[Dict],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache autocomplete suggestions"""
        try:
            cache_key = f"{self.PREFIX_AUTOCOMPLETE}:{prefix.lower()}"
            ttl = ttl or self.TTL_AUTOCOMPLETE
            cache.set(cache_key, suggestions, ttl)
            return True
        except Exception as e:
            logger.error(f"Error caching autocomplete: {e}")
            return False
    
    def get_popular_queries(self, limit: int = 10) -> Optional[List[Dict]]:
        """Get cached popular queries"""
        cache_key = f"{self.PREFIX_POPULAR}:queries:{limit}"
        return cache.get(cache_key)
    
    def set_popular_queries(
        self,
        queries: List[Dict],
        limit: int = 10,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache popular queries"""
        try:
            cache_key = f"{self.PREFIX_POPULAR}:queries:{limit}"
            ttl = ttl or self.TTL_POPULAR_QUERIES
            cache.set(cache_key, queries, ttl)
            return True
        except Exception as e:
            logger.error(f"Error caching popular queries: {e}")
            return False
    
    def invalidate_search_cache(self, pattern: Optional[str] = None):
        """
        Invalidate search cache
        
        Args:
            pattern: Optional pattern to match keys (e.g., 'search:*')
        """
        if pattern is None:
            pattern = f"{self.PREFIX_SEARCH}:*"
        
        try:
            # Note: This requires Redis
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            keys = redis_conn.keys(pattern)
            if keys:
                redis_conn.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache keys: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
    
    def warm_cache(self, popular_queries: List[str]):
        """
        Warm cache with popular queries
        
        Args:
            popular_queries: List of popular query strings
        """
        from .hybrid_search import HybridSearchService
        
        search_service = HybridSearchService()
        
        logger.info(f"Warming cache with {len(popular_queries)} queries")
        
        for query in popular_queries:
            try:
                # Execute search
                results = search_service.search(
                    query=query,
                    page=1,
                    page_size=20
                )
                
                # Cache results
                cache_key = self.generate_search_cache_key(
                    query=query,
                    filters={},
                    page=1,
                    page_size=20,
                    sort_by='relevance'
                )
                
                self.set_search_results(cache_key, results)
                
                logger.debug(f"Cached query: {query}")
            
            except Exception as e:
                logger.error(f"Error warming cache for query '{query}': {e}")
        
        logger.info("Cache warming completed")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics dict
        """
        try:
            from django_redis import get_redis_connection
            redis_conn = get_redis_connection("default")
            
            info = redis_conn.info('stats')
            
            return {
                'total_commands': info.get('total_commands_processed', 0),
                'total_connections': info.get('total_connections_received', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                ),
                'used_memory': info.get('used_memory_human', 'N/A'),
                'connected_clients': redis_conn.client_list().__len__()
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100
```

**Checklist:**
- [ ] Create serializers
- [ ] Implement API views
- [ ] Add caching layer
- [ ] Configure rate limiting
- [ ] Add health check endpoint
- [ ] Write API tests
- [ ] Generate API documentation

---

**Продолжить с Task 5.4: URL Configuration & API Documentation?**