Отлично! Продолжаю с Application-Level Optimization и завершающими разделами: Cost Optimization, Disaster Recovery, и Production Readiness Checklist. Это будут файлы 13-16, которые завершат всю серию Deep-Dive документации.

Структура:
1. ФАЙЛ 13: Application-Level Optimization (Django, Python, async)
2. ФАЙЛ 14: Cost Optimization (cloud costs, resource usage)
3. ФАЙЛ 15: Disaster Recovery (backups, failover, restoration)
4. ФАЙЛ 16: Production Readiness Checklist (финальный чеклист)

Начнем!# 🎯 DEEP-DIVE: SEARCH SYSTEM (APPLICATION OPTIMIZATION)

## ФАЙЛ 13: `docs/deep-dive/search/APPLICATION_OPTIMIZATION.md`

```markdown
# Application-Level Optimization - Deep Dive

## 🚀 Django & Python Optimization

### Django Settings Optimization

```python
# ios_core/settings/production.py

"""
Production settings with optimizations
"""

import os
from .base import *

# ============================================================================
# SECURITY
# ============================================================================

DEBUG = False
ALLOWED_HOSTS = ['ios.example.com', 'api.ios.example.com']

SECRET_KEY = os.environ.get('SECRET_KEY')

# ============================================================================
# DATABASE
# ============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', 5432),
        
        # Connection pooling
        'CONN_MAX_AGE': 600,  # 10 minutes
        
        # Performance options
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30s timeout
        },
        
        # Persistent connections
        'ATOMIC_REQUESTS': False,  # Don't wrap in transaction
    },
    
    # Read replicas
    'replica_1': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_REPLICA_1_HOST'),
        # ... same config
    },
    'replica_2': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DB_REPLICA_2_HOST'),
        # ... same config
    },
}

DATABASE_ROUTERS = ['ios_core.database_router.ReadWriteRouter']

# ============================================================================
# CACHE
# ============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            
            # Connection pool
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            
            # Serializer (pickle is faster than json)
            'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
            
            # Compression
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            
            # Socket timeout
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'ios',
        'TIMEOUT': 3600,  # 1 hour default
    }
}

# ============================================================================
# MIDDLEWARE OPTIMIZATION
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # Compress responses
    
    # Custom middleware for performance
    'ios_core.middleware.RequestTimingMiddleware',
    'ios_core.middleware.CacheControlMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ============================================================================
# TEMPLATES
# ============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'loaders': [
                # Cached template loader (production)
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============================================================================
# STATIC FILES
# ============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/static/'

# Use whitenoise for efficient static file serving
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================================================================
# LOGGING
# ============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ios/django.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'ios_core': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# ============================================================================
# CELERY
# ============================================================================

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

CELERY_TASK_SERIALIZER = 'pickle'  # Faster than json
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = ['pickle', 'json']

CELERY_TASK_COMPRESSION = 'gzip'
CELERY_RESULT_COMPRESSION = 'gzip'

# Task optimization
CELERY_TASK_ACKS_LATE = True  # Acknowledge after completion
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Time limits
CELERY_TASK_SOFT_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_TIME_LIMIT = 600  # 10 minutes

# ============================================================================
# REST FRAMEWORK
# ============================================================================

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        # Remove BrowsableAPIRenderer in production
    ],
    
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    
    # Pagination
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    
    # Throttling
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'search': '500/hour',
    },
    
    # Performance
    'EXCEPTION_HANDLER': 'ios_core.exceptions.custom_exception_handler',
}
```

### Custom Middleware

```python
# ios_core/middleware.py

"""
Custom middleware for performance optimization
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache

logger = logging.getLogger(__name__)

class RequestTimingMiddleware(MiddlewareMixin):
    """
    Measure request processing time
    
    Adds X-Request-Time header with duration in ms
    Logs slow requests
    """
    
    def process_request(self, request):
        """Record start time"""
        request._start_time = time.time()
    
    def process_response(self, request, response):
        """Calculate duration and add header"""
        if hasattr(request, '_start_time'):
            duration_ms = (time.time() - request._start_time) * 1000
            
            # Add header
            response['X-Request-Time'] = f"{duration_ms:.2f}ms"
            
            # Log slow requests
            if duration_ms > 1000:  # > 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration_ms:.0f}ms"
                )
        
        return response


class CacheControlMiddleware(MiddlewareMixin):
    """
    Add cache control headers
    
    Optimizes caching for different content types
    """
    
    def process_response(self, request, response):
        """Add cache control headers"""
        path = request.path
        
        # Static files: long cache
        if path.startswith('/static/'):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
        
        # API endpoints: no cache by default
        elif path.startswith('/api/'):
            # Search results: short cache
            if 'search' in path:
                response['Cache-Control'] = 'private, max-age=300'  # 5 min
            else:
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Custom rate limiting middleware
    
    More flexible than DRF throttling
    """
    
    def process_request(self, request):
        """Check rate limits"""
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check different limits for different endpoints
        if request.path.startswith('/api/search/'):
            limit = 10  # 10 requests per minute
            window = 60
            key = f'ratelimit:search:{client_id}'
        else:
            limit = 100
            window = 60
            key = f'ratelimit:api:{client_id}'
        
        # Check limit
        current = cache.get(key, 0)
        
        if current >= limit:
            from django.http import JsonResponse
            return JsonResponse(
                {'error': 'Rate limit exceeded'},
                status=429
            )
        
        # Increment counter
        cache.set(key, current + 1, window)
        
        return None
    
    def get_client_id(self, request):
        """Get client identifier (IP or user)"""
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Get IP from X-Forwarded-For or REMOTE_ADDR
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        return f"ip:{ip}"
```

---

## ⚡ Async & Concurrency

### Async Views (Django 4.1+)

```python
# search/views_async.py

"""
Async views for better concurrency
"""

import asyncio
from django.http import JsonResponse
from django.views import View
from asgiref.sync import sync_to_async

class AsyncSearchView(View):
    """
    Async search view
    
    Benefits:
    - Non-blocking I/O
    - Handle more concurrent requests
    - Better resource utilization
    """
    
    async def post(self, request):
        """
        Async search handler
        
        Performs ES and Qdrant searches concurrently
        """
        import json
        data = json.loads(request.body)
        query = data.get('query', '')
        
        # Execute searches concurrently
        es_task = self.search_elasticsearch(query)
        qdrant_task = self.search_qdrant(query)
        
        # Wait for both to complete
        es_results, qdrant_results = await asyncio.gather(
            es_task,
            qdrant_task,
            return_exceptions=True
        )
        
        # Merge results
        merged = self.merge_results(es_results, qdrant_results)
        
        return JsonResponse({
            'results': merged,
            'total': len(merged)
        })
    
    async def search_elasticsearch(self, query: str):
        """Async Elasticsearch search"""
        from elasticsearch import AsyncElasticsearch
        
        client = AsyncElasticsearch(['http://localhost:9200'])
        
        try:
            response = await client.search(
                index='ios-documents',
                body={
                    'query': {
                        'multi_match': {
                            'query': query,
                            'fields': ['title^3', 'content']
                        }
                    },
                    'size': 10
                }
            )
            
            return response['hits']['hits']
        
        finally:
            await client.close()
    
    async def search_qdrant(self, query: str):
        """Async Qdrant search"""
        # Generate embedding (in separate thread to not block)
        embedding = await sync_to_async(self.generate_embedding)(query)
        
        # Qdrant doesn't have async client yet, so use thread pool
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host='localhost', port=6333)
        
        results = await sync_to_async(client.search)(
            collection_name='ios-embeddings',
            query_vector=embedding,
            limit=10
        )
        
        return results
    
    def generate_embedding(self, text: str):
        """Generate embedding (CPU-bound, use thread)"""
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return model.encode(text).tolist()
    
    def merge_results(self, es_results, qdrant_results):
        """Merge and deduplicate results"""
        # Implementation here
        return []
```

### Celery Task Optimization

```python
# search/tasks.py

"""
Optimized Celery tasks
"""

from celery import shared_task, group, chord
from celery.utils.log import get_task_logger
import time

logger = get_task_logger(__name__)

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=300,
    soft_time_limit=240
)
def index_document(self, document_id: int):
    """
    Index single document
    
    Features:
    - Automatic retry on failure
    - Time limits
    - Error handling
    """
    try:
        from ios_core.models import Document
        from search.indexing import SearchIndexer
        
        document = Document.objects.get(id=document_id)
        indexer = SearchIndexer()
        
        # Index in Elasticsearch
        indexer.index_document_elasticsearch(document)
        
        # Generate and index embedding
        indexer.index_document_qdrant(document)
        
        logger.info(f"Indexed document {document_id}")
        
        return {'document_id': document_id, 'status': 'success'}
    
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        return {'document_id': document_id, 'status': 'not_found'}
    
    except Exception as exc:
        logger.error(f"Error indexing document {document_id}: {exc}")
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def batch_index_documents(document_ids: list):
    """
    Index multiple documents in parallel
    
    Uses Celery group for parallelism
    """
    # Create parallel tasks
    job = group(
        index_document.s(doc_id)
        for doc_id in document_ids
    )
    
    # Execute
    result = job.apply_async()
    
    return {
        'total': len(document_ids),
        'task_id': result.id
    }


@shared_task
def index_all_documents_chunked():
    """
    Index all documents in chunks
    
    More memory-efficient than loading all at once
    """
    from ios_core.models import Document
    from django.db.models import QuerySet
    
    chunk_size = 1000
    total_indexed = 0
    
    # Iterate in chunks
    queryset = Document.objects.all().order_by('id')
    
    for chunk in queryset_chunks(queryset, chunk_size):
        document_ids = [doc.id for doc in chunk]
        
        # Index chunk in parallel
        batch_index_documents.delay(document_ids)
        
        total_indexed += len(document_ids)
        logger.info(f"Queued {total_indexed} documents for indexing")
    
    return {'total_indexed': total_indexed}


def queryset_chunks(queryset: QuerySet, chunk_size: int):
    """
    Iterate queryset in chunks
    
    Memory-efficient iteration
    """
    pk = 0
    last_pk = queryset.order_by('-pk').first().pk
    
    while pk < last_pk:
        chunk = queryset.filter(pk__gt=pk)[:chunk_size]
        pk = chunk.last().pk
        yield chunk


# Periodic task for cache warmup
@shared_task
def warmup_popular_queries():
    """
    Warm up cache for popular queries
    
    Runs daily to keep cache hot
    """
    from search.analytics import get_popular_queries
    from search.views import SearchView
    
    popular = get_popular_queries(limit=100)
    
    for query_text in popular:
        # Execute search (will populate cache)
        try:
            # This would normally be called via HTTP
            # Here we simulate it
            logger.info(f"Warming cache for: {query_text}")
            
            # Your search logic here
            # ...
            
        except Exception as e:
            logger.error(f"Error warming cache for '{query_text}': {e}")
    
    return {'warmed': len(popular)}
```

---

## 🔄 Connection Pooling

### Database Connection Pool

```python
# ios_core/database_pool.py

"""
Advanced database connection pooling
"""

from django.db.backends.postgresql.base import DatabaseWrapper
import psycopg2.pool

class PooledDatabaseWrapper(DatabaseWrapper):
    """
    PostgreSQL connection pool
    
    Reuses connections instead of creating new ones
    """
    
    _connection_pools = {}
    
    def get_new_connection(self, conn_params):
        """Get connection from pool"""
        pool_key = self._get_pool_key(conn_params)
        
        if pool_key not in self._connection_pools:
            # Create pool
            self._connection_pools[pool_key] = psycopg2.pool.ThreadedConnectionPool(
                minconn=5,
                maxconn=20,
                **conn_params
            )
        
        pool = self._connection_pools[pool_key]
        return pool.getconn()
    
    def _get_pool_key(self, conn_params):
        """Generate unique key for pool"""
        return f"{conn_params['host']}:{conn_params['port']}/{conn_params['database']}"


# Update settings to use pooled wrapper
# DATABASES = {
#     'default': {
#         'ENGINE': 'ios_core.database_pool.PooledDatabaseWrapper',
#         ...
#     }
# }
```

### HTTP Connection Pool

```python
# ios_core/http_client.py

"""
HTTP client with connection pooling
"""

import httpx
from typing import Optional

class HTTPClient:
    """
    Singleton HTTP client with connection pooling
    
    Reuses connections for better performance
    """
    
    _instance: Optional[httpx.Client] = None
    _async_instance: Optional[httpx.AsyncClient] = None
    
    @classmethod
    def get_client(cls) -> httpx.Client:
        """Get sync HTTP client"""
        if cls._instance is None:
            cls._instance = httpx.Client(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                http2=True  # Use HTTP/2 for better performance
            )
        
        return cls._instance
    
    @classmethod
    def get_async_client(cls) -> httpx.AsyncClient:
        """Get async HTTP client"""
        if cls._async_instance is None:
            cls._async_instance = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0
                ),
                http2=True
            )
        
        return cls._async_instance
    
    @classmethod
    def close_all(cls):
        """Close all clients"""
        if cls._instance:
            cls._instance.close()
            cls._instance = None
        
        if cls._async_instance:
            import asyncio
            asyncio.run(cls._async_instance.aclose())
            cls._async_instance = None


# Usage
client = HTTPClient.get_client()
response = client.get('https://api.example.com/data')
```

---

## 📊 Monitoring & Profiling

### Performance Monitoring

```python
# ios_core/monitoring.py

"""
Performance monitoring and profiling
"""

import time
import functools
from prometheus_client import Counter, Histogram, Gauge
import logging

logger = logging.getLogger(__name__)

# Prometheus metrics
search_requests_total = Counter(
    'search_requests_total',
    'Total search requests',
    ['endpoint', 'status']
)

search_duration_seconds = Histogram(
    'search_duration_seconds',
    'Search request duration',
    ['endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

active_searches = Gauge(
    'active_searches',
    'Number of active search requests'
)

cache_hits = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_type']
)

cache_misses = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_type']
)


def monitor_performance(func):
    """
    Decorator to monitor function performance
    
    Tracks:
    - Execution time
    - Success/failure rate
    - Active requests
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Track active requests
        active_searches.inc()
        
        start_time = time.time()
        endpoint = func.__name__
        status = 'success'
        
        try:
            result = func(*args, **kwargs)
            return result
        
        except Exception as e:
            status = 'error'
            logger.error(f"Error in {endpoint}: {e}")
            raise
        
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            search_requests_total.labels(
                endpoint=endpoint,
                status=status
            ).inc()
            
            search_duration_seconds.labels(
                endpoint=endpoint
            ).observe(duration)
            
            active_searches.dec()
            
            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {endpoint} took {duration:.2f}s"
                )
    
    return wrapper


def profile_function(func):
    """
    Decorator to profile function execution
    
    Use in development to find bottlenecks
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        import cProfile
        import pstats
        from io import StringIO
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func(*args, **kwargs)
        
        profiler.disable()
        
        # Print stats
        s = StringIO()
        stats = pstats.Stats(profiler, stream=s)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 functions
        
        print(f"\n{'='*60}")
        print(f"Profile for: {func.__name__}")
        print(f"{'='*60}")
        print(s.getvalue())
        
        return result
    
    return wrapper


# Usage examples
@monitor_performance
def search_documents(query: str):
    """Search with monitoring"""
    # Your search logic
    pass


@profile_function
def expensive_operation():
    """Profile this function"""
    # Your code
    pass
```

### Memory Profiling

```python
# scripts/profile_memory.py

"""
Memory profiling for search operations
"""

from memory_profiler import profile
import gc

@profile
def profile_search_memory():
    """
    Profile memory usage during search
    
    Run with:
        python -m memory_profiler scripts/profile_memory.py
    """
    from search.search_service import HybridSearchService
    
    service = HybridSearchService()
    
    # Run multiple searches
    queries = [
        "persönliches budget",
        "hilfe bei behinderung",
        "pflegegeld antrag"
    ]
    
    for query in queries:
        results = service.hybrid_search(query=query, limit=10)
        print(f"Query: {query}, Results: {len(results)}")
        
        # Force garbage collection
        gc.collect()


@profile
def profile_bulk_indexing():
    """Profile memory during bulk indexing"""
    from ios_core.models import Document
    from search.indexing import SearchIndexer
    
    indexer = SearchIndexer()
    
    # Get documents in chunks
    chunk_size = 100
    queryset = Document.objects.all()[:1000]
    
    for i in range(0, 1000, chunk_size):
        chunk = queryset[i:i+chunk_size]
        
        for doc in chunk:
            indexer.index_document_elasticsearch(doc)
        
        print(f"Indexed {i+chunk_size} documents")
        gc.collect()


if __name__ == '__main__':
    print("Profiling search memory...")
    profile_search_memory()
    
    print("\nProfiling bulk indexing...")
    profile_bulk_indexing()
```

---

## 🎯 Code Optimization Tips

### Python Best Practices

```python
# optimization_examples.py

"""
Python optimization examples
"""

# ============================================================================
# 1. Use list comprehensions instead of loops
# ============================================================================

# SLOW
results = []
for item in data:
    if item.score > 0.5:
        results.append(item.title)

# FAST
results = [item.title for item in data if item.score > 0.5]

# ============================================================================
# 2. Use generators for large datasets
# ============================================================================

# SLOW: Loads all in memory
def get_all_documents():
    return Document.objects.all()

# FAST: Lazy evaluation
def get_all_documents_generator():
    for doc in Document.objects.all().iterator():
        yield doc

# ============================================================================
# 3. Use sets for membership testing
# ============================================================================

# SLOW: O(n)
if item in my_list:
    pass

# FAST: O(1)
if item in my_set:
    pass

# ============================================================================
# 4. Use dict.get() with default
# ============================================================================

# SLOW
if key in my_dict:
    value = my_dict[key]
else:
    value = default

# FAST
value = my_dict.get(key, default)

# ============================================================================
# 5. Use join() instead of string concatenation
# ============================================================================

# SLOW
result = ""
for item in items:
    result += item + " "

# FAST
result = " ".join(items)

# ============================================================================
# 6. Cache expensive computations
# ============================================================================

from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_function(param):
    # Expensive computation
    return result

# ============================================================================
# 7. Use slots for memory-efficient classes
# ============================================================================

# SLOW: Uses dict for attributes
class Document:
    def __init__(self, title, content):
        self.title = title
        self.content = content

# FAST: Uses slots (less memory)
class Document:
    __slots__ = ['title', 'content']
    
    def __init__(self, title, content):
        self.title = title
        self.content = content

# ============================================================================
# 8. Use enumerate() instead of range(len())
# ============================================================================

# SLOW
for i in range(len(items)):
    item = items[i]
    print(f"{i}: {item}")

# FAST
for i, item in enumerate(items):
    print(f"{i}: {item}")

# ============================================================================
# 9. Use defaultdict for grouping
# ============================================================================

from collections import defaultdict

# SLOW
groups = {}
for item in items:
    if item.category not in groups:
        groups[item.category] = []
    groups[item.category].append(item)

# FAST
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)

# ============================================================================
# 10. Use map() for transformations
# ============================================================================

# SLOW
results = []
for item in items:
    results.append(transform(item))

# FAST
results = list(map(transform, items))

# FASTEST (for simple operations)
results = [transform(item) for item in items]
```

---

**Продолжение следует...**

Создано:
- ✅ Django production settings optimization
- ✅ Custom middleware (timing, caching, rate limiting)
- ✅ Async views and Celery task optimization
- ✅ Connection pooling (DB, HTTP)
- ✅ Performance monitoring with Prometheus
- ✅ Memory profiling
- ✅ Python optimization best practices

**Следующие файлы:**
1. ФАЙЛ 14: Cost Optimization
2. ФАЙЛ 15: Disaster Recovery
3. ФАЙЛ 16: Production Readiness Checklist (финал!)

**Готовы продолжить с Cost Optimization?**