Пользователь хочет продолжить с Task 2.2: Integration Testing. Продолжу детальное описание задач Sprint 2.## ФАЙЛ 19 (продолжение): Integration Testing и Sprint 3-4

```markdown
# Phase Implementation Details (продолжение)

#### Task 2.2: Integration Testing Setup
**Assignee:** Backend Developer
**Time:** 2 days
**Priority:** High

**Integration Test Suite:**

```python
# tests/integration/test_database_integration.py

"""
Integration tests for database operations
"""

import pytest
from django.test import TransactionTestCase
from search.models import Document, SearchQuery, UserPreference, ClickEvent
from django.contrib.auth.models import User
from datetime import datetime, timedelta

@pytest.mark.integration
class TestDocumentDatabaseIntegration(TransactionTestCase):
    """Test Document model database integration"""
    
    def setUp(self):
        """Setup test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_bulk_document_creation(self):
        """Test bulk creating documents"""
        documents = [
            Document(
                title=f'Document {i}',
                content=f'Content {i}',
                document_type=Document.DocumentType.LAW,
                category='Test',
                is_active=True
            )
            for i in range(1000)
        ]
        
        created = Document.objects.bulk_create(documents)
        
        assert len(created) == 1000
        assert Document.objects.count() == 1000
    
    def test_complex_query_with_filters(self):
        """Test complex queries with multiple filters"""
        # Create test documents
        Document.objects.bulk_create([
            Document(
                title='SGB IX Document',
                content='Content about disability law',
                document_type=Document.DocumentType.LAW,
                legal_code='SGB IX',
                category='Disability',
                is_active=True
            ),
            Document(
                title='SGB XI Document',
                content='Content about care insurance',
                document_type=Document.DocumentType.LAW,
                legal_code='SGB XI',
                category='Care',
                is_active=True
            ),
            Document(
                title='Inactive Document',
                content='Content',
                document_type=Document.DocumentType.LAW,
                legal_code='SGB IX',
                category='Disability',
                is_active=False
            )
        ])
        
        # Complex query
        results = Document.objects.filter(
            legal_code='SGB IX',
            is_active=True,
            document_type=Document.DocumentType.LAW
        ).order_by('-created_at')
        
        assert results.count() == 1
        assert results.first().title == 'SGB IX Document'
    
    def test_search_query_tracking_with_clicks(self):
        """Test search query tracking with click events"""
        # Create document
        doc = Document.objects.create(
            title='Test Document',
            content='Content',
            document_type=Document.DocumentType.LAW,
            category='Test'
        )
        
        # Create search query
        query = SearchQuery.objects.create(
            query_text='test query',
            query_normalized='test query',
            session_id='test-session',
            total_results=1,
            results_returned=1,
            search_time_ms=100
        )
        
        # Create click event
        click = ClickEvent.objects.create(
            search_query=query,
            document=doc,
            position=1,
            score=0.95,
            dwell_time_seconds=30
        )
        
        # Verify relationships
        assert query.click_events.count() == 1
        assert doc.click_events.count() == 1
        assert click.search_query == query
        assert click.document == doc
    
    def test_user_preferences_with_favorites(self):
        """Test user preferences with favorite documents"""
        # Create preference
        pref = UserPreference.objects.create(
            user=self.user,
            language_preference='de'
        )
        
        # Create documents
        docs = Document.objects.bulk_create([
            Document(
                title=f'Document {i}',
                content='Content',
                document_type=Document.DocumentType.LAW,
                category='Test'
            )
            for i in range(5)
        ])
        
        # Add favorites
        pref.favorite_documents.add(*docs[:3])
        
        assert pref.favorite_documents.count() == 3
        assert list(pref.favorite_documents.all()) == docs[:3]
    
    def test_document_statistics_increment(self):
        """Test atomic increment of view/click counts"""
        doc = Document.objects.create(
            title='Test Document',
            content='Content',
            document_type=Document.DocumentType.LAW,
            category='Test'
        )
        
        initial_views = doc.view_count
        initial_clicks = doc.click_count
        
        # Simulate concurrent increments
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection):
            doc.increment_view_count()
            doc.increment_click_count()
        
        doc.refresh_from_db()
        
        assert doc.view_count == initial_views + 1
        assert doc.click_count == initial_clicks + 1
    
    def test_query_performance_with_indexes(self):
        """Test query performance with proper indexes"""
        import time
        
        # Create 10,000 documents
        documents = [
            Document(
                title=f'Document {i}',
                content=f'Content {i}',
                document_type=Document.DocumentType.LAW,
                legal_code='SGB IX',
                category='Test',
                is_active=True
            )
            for i in range(10000)
        ]
        Document.objects.bulk_create(documents)
        
        # Test indexed query performance
        start = time.time()
        results = Document.objects.filter(
            legal_code='SGB IX',
            is_active=True
        )[:100]
        list(results)  # Force evaluation
        elapsed = time.time() - start
        
        # Should be fast with indexes
        assert elapsed < 0.1  # Less than 100ms
```

```python
# tests/integration/test_elasticsearch_integration.py

"""
Integration tests for Elasticsearch
"""

import pytest
from elasticsearch import Elasticsearch
from search.models import Document
from search.services.elasticsearch_service import ElasticsearchService
import time

@pytest.mark.integration
@pytest.mark.elasticsearch
class TestElasticsearchIntegration:
    """Test Elasticsearch integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Elasticsearch for tests"""
        self.es_client = Elasticsearch(['http://localhost:9200'])
        self.service = ElasticsearchService()
        
        # Create test index
        self.index_name = 'test-ios-documents'
        
        # Delete if exists
        if self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.delete(index=self.index_name)
        
        # Create index with mapping
        self.es_client.indices.create(
            index=self.index_name,
            body={
                'settings': {
                    'number_of_shards': 1,
                    'number_of_replicas': 0,
                    'analysis': {
                        'analyzer': {
                            'german_analyzer': {
                                'type': 'german'
                            }
                        }
                    }
                },
                'mappings': {
                    'properties': {
                        'title': {
                            'type': 'text',
                            'analyzer': 'german_analyzer',
                            'fields': {
                                'keyword': {'type': 'keyword'}
                            }
                        },
                        'content': {
                            'type': 'text',
                            'analyzer': 'german_analyzer'
                        },
                        'document_type': {'type': 'keyword'},
                        'category': {'type': 'keyword'},
                        'legal_code': {'type': 'keyword'},
                        'paragraph': {'type': 'keyword'},
                        'tags': {'type': 'keyword'},
                        'created_at': {'type': 'date'},
                        'is_active': {'type': 'boolean'}
                    }
                }
            }
        )
        
        yield
        
        # Cleanup
        if self.es_client.indices.exists(index=self.index_name):
            self.es_client.indices.delete(index=self.index_name)
    
    def test_index_document(self):
        """Test indexing a document"""
        doc_id = 'test-doc-1'
        document = {
            'title': 'Test Dokument',
            'content': 'Dies ist ein Test-Dokument über Sozialrecht',
            'document_type': 'LAW',
            'category': 'Sozialrecht',
            'legal_code': 'SGB IX',
            'is_active': True
        }
        
        # Index document
        result = self.es_client.index(
            index=self.index_name,
            id=doc_id,
            document=document
        )
        
        assert result['result'] in ['created', 'updated']
        
        # Refresh index
        self.es_client.indices.refresh(index=self.index_name)
        
        # Verify document exists
        doc = self.es_client.get(index=self.index_name, id=doc_id)
        assert doc['_source']['title'] == 'Test Dokument'
    
    def test_bulk_indexing(self):
        """Test bulk indexing performance"""
        from elasticsearch.helpers import bulk
        
        # Prepare 1000 documents
        documents = [
            {
                '_index': self.index_name,
                '_id': f'doc-{i}',
                '_source': {
                    'title': f'Dokument {i}',
                    'content': f'Inhalt für Dokument {i} über Sozialrecht',
                    'document_type': 'LAW',
                    'category': 'Test',
                    'is_active': True
                }
            }
            for i in range(1000)
        ]
        
        # Bulk index
        start = time.time()
        success, failed = bulk(self.es_client, documents)
        elapsed = time.time() - start
        
        assert success == 1000
        assert failed == 0
        assert elapsed < 5.0  # Should complete in < 5 seconds
        
        # Refresh and verify count
        self.es_client.indices.refresh(index=self.index_name)
        count = self.es_client.count(index=self.index_name)
        assert count['count'] == 1000
    
    def test_search_german_text(self):
        """Test German text search with analyzer"""
        # Index German documents
        documents = [
            {
                'title': 'Persönliches Budget',
                'content': 'Das Persönliche Budget ermöglicht Menschen mit Behinderungen...',
                'legal_code': 'SGB IX'
            },
            {
                'title': 'Pflegeversicherung',
                'content': 'Die Pflegeversicherung bietet Unterstützung...',
                'legal_code': 'SGB XI'
            }
        ]
        
        for i, doc in enumerate(documents):
            self.es_client.index(
                index=self.index_name,
                id=f'doc-{i}',
                document=doc
            )
        
        self.es_client.indices.refresh(index=self.index_name)
        
        # Search with German stemming
        result = self.es_client.search(
            index=self.index_name,
            body={
                'query': {
                    'multi_match': {
                        'query': 'persönlich',  # Should match "Persönliches"
                        'fields': ['title^2', 'content'],
                        'analyzer': 'german_analyzer'
                    }
                }
            }
        )
        
        assert result['hits']['total']['value'] == 1
        assert 'Persönliches Budget' in result['hits']['hits'][0]['_source']['title']
    
    def test_filtered_search(self):
        """Test search with filters"""
        # Index documents with different types
        docs = [
            {'title': 'Law 1', 'document_type': 'LAW', 'legal_code': 'SGB IX'},
            {'title': 'Law 2', 'document_type': 'LAW', 'legal_code': 'SGB XI'},
            {'title': 'Court Decision', 'document_type': 'COURT', 'legal_code': 'SGB IX'}
        ]
        
        for i, doc in enumerate(docs):
            self.es_client.index(index=self.index_name, id=f'doc-{i}', document=doc)
        
        self.es_client.indices.refresh(index=self.index_name)
        
        # Search with filters
        result = self.es_client.search(
            index=self.index_name,
            body={
                'query': {
                    'bool': {
                        'must': {'match_all': {}},
                        'filter': [
                            {'term': {'document_type': 'LAW'}},
                            {'term': {'legal_code': 'SGB IX'}}
                        ]
                    }
                }
            }
        )
        
        assert result['hits']['total']['value'] == 1
        assert result['hits']['hits'][0]['_source']['title'] == 'Law 1'
    
    def test_aggregations(self):
        """Test aggregations for faceted search"""
        # Index documents
        for i in range(100):
            self.es_client.index(
                index=self.index_name,
                id=f'doc-{i}',
                document={
                    'title': f'Document {i}',
                    'document_type': 'LAW' if i % 2 == 0 else 'COURT',
                    'legal_code': f'SGB {(i % 3) + 1}'
                }
            )
        
        self.es_client.indices.refresh(index=self.index_name)
        
        # Search with aggregations
        result = self.es_client.search(
            index=self.index_name,
            body={
                'size': 0,
                'aggs': {
                    'by_type': {
                        'terms': {'field': 'document_type'}
                    },
                    'by_code': {
                        'terms': {'field': 'legal_code'}
                    }
                }
            }
        )
        
        assert 'aggregations' in result
        assert len(result['aggregations']['by_type']['buckets']) == 2
        assert len(result['aggregations']['by_code']['buckets']) == 3
```

```python
# tests/integration/test_qdrant_integration.py

"""
Integration tests for Qdrant vector search
"""

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

@pytest.mark.integration
@pytest.mark.qdrant
class TestQdrantIntegration:
    """Test Qdrant integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Qdrant for tests"""
        self.client = QdrantClient(host='localhost', port=6333)
        self.collection_name = 'test-ios-vectors'
        
        # Delete collection if exists
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except:
            pass
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
        yield
        
        # Cleanup
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except:
            pass
    
    def test_insert_vectors(self):
        """Test inserting vectors"""
        # Create sample vectors
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(10)
        ]
        
        # Insert points
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={'title': f'Document {i}'}
            )
            for i, vec in enumerate(vectors)
        ]
        
        result = self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        assert result.status == 'completed'
        
        # Verify count
        info = self.client.get_collection(collection_name=self.collection_name)
        assert info.points_count == 10
    
    def test_similarity_search(self):
        """Test similarity search"""
        # Insert vectors
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(100)
        ]
        
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={
                    'title': f'Document {i}',
                    'legal_code': f'SGB {(i % 3) + 1}'
                }
            )
            for i, vec in enumerate(vectors)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Search with query vector
        query_vector = np.random.rand(384).tolist()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10
        )
        
        assert len(results) == 10
        assert all(hasattr(r, 'score') for r in results)
        assert all(0 <= r.score <= 1 for r in results)
    
    def test_filtered_search(self):
        """Test search with payload filters"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Insert vectors with metadata
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(50)
        ]
        
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={
                    'title': f'Document {i}',
                    'document_type': 'LAW' if i % 2 == 0 else 'COURT',
                    'legal_code': 'SGB IX'
                }
            )
            for i, vec in enumerate(vectors)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Search with filter
        query_vector = np.random.rand(384).tolist()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key='document_type',
                        match=MatchValue(value='LAW')
                    )
                ]
            ),
            limit=10
        )
        
        assert len(results) <= 10
        assert all(r.payload['document_type'] == 'LAW' for r in results)
    
    def test_batch_upload_performance(self):
        """Test batch upload performance"""
        import time
        
        # Generate 10,000 vectors
        batch_size = 1000
        total_vectors = 10000
        
        start = time.time()
        
        for batch_start in range(0, total_vectors, batch_size):
            batch_end = min(batch_start + batch_size, total_vectors)
            
            vectors = [
                np.random.rand(384).tolist()
                for _ in range(batch_end - batch_start)
            ]
            
            points = [
                PointStruct(
                    id=batch_start + i,
                    vector=vec,
                    payload={'doc_id': batch_start + i}
                )
                for i, vec in enumerate(vectors)
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 30.0  # Less than 30 seconds
        
        # Verify count
        info = self.client.get_collection(collection_name=self.collection_name)
        assert info.points_count == total_vectors
```

```python
# tests/integration/test_redis_integration.py

"""
Integration tests for Redis caching
"""

import pytest
import redis
import time
import json

@pytest.mark.integration
class TestRedisIntegration:
    """Test Redis integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Redis for tests"""
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=1,  # Use different DB for tests
            decode_responses=True
        )
        
        # Flush test database
        self.redis_client.flushdb()
        
        yield
        
        # Cleanup
        self.redis_client.flushdb()
    
    def test_basic_cache_operations(self):
        """Test basic cache set/get operations"""
        key = 'test:key'
        value = 'test value'
        
        # Set
        self.redis_client.setex(key, 60, value)
        
        # Get
        retrieved = self.redis_client.get(key)
        assert retrieved == value
        
        # TTL
        ttl = self.redis_client.ttl(key)
        assert 50 < ttl <= 60
    
    def test_cache_json_data(self):
        """Test caching JSON data"""
        key = 'test:json'
        data = {
            'query': 'test',
            'results': [1, 2, 3],
            'total': 3
        }
        
        # Cache JSON
        self.redis_client.setex(
            key,
            300,
            json.dumps(data)
        )
        
        # Retrieve and parse
        retrieved = json.loads(self.redis_client.get(key))
        assert retrieved == data
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        key = 'test:expire'
        value = 'temporary'
        
        # Set with 1 second TTL
        self.redis_client.setex(key, 1, value)
        
        # Should exist immediately
        assert self.redis_client.get(key) == value
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be gone
        assert self.redis_client.get(key) is None
    
    def test_cache_invalidation_pattern(self):
        """Test cache invalidation by pattern"""
        # Set multiple keys
        for i in range(10):
            self.redis_client.set(f'search:query:{i}', f'result {i}')
        
        # Add some other keys
        self.redis_client.set('other:key', 'value')
        
        # Delete by pattern
        keys = self.redis_client.keys('search:query:*')
        if keys:
            self.redis_client.delete(*keys)
        
        # Verify deletion
        assert len(self.redis_client.keys('search:query:*')) == 0
        assert self.redis_client.get('other:key') == 'value'
    
    def test_atomic_increment(self):
        """Test atomic counter increment"""
        key = 'test:counter'
        
        # Increment multiple times
        for _ in range(100):
            self.redis_client.incr(key)
        
        # Verify final value
        assert int(self.redis_client.get(key)) == 100
    
    def test_list_operations(self):
        """Test Redis list operations for autocomplete"""
        key = 'autocomplete:suggestions'
        
        # Add suggestions
        suggestions = ['persönlich', 'pflege', 'paragraph', 'personal']
        for suggestion in suggestions:
            self.redis_client.lpush(key, suggestion)
        
        # Get all
        all_suggestions = self.redis_client.lrange(key, 0, -1)
        assert len(all_suggestions) == 4
        
        # Get top 2
        top_2 = self.redis_client.lrange(key, 0, 1)
        assert len(top_2) == 2
    
    def test_sorted_set_for_popular_queries(self):
        """Test sorted sets for tracking popular queries"""
        key = 'popular:queries'
        
        # Add queries with scores (frequency)
        queries = {
            'persönliches budget': 100,
            'pflege': 80,
            'sgb ix': 60,
            'behinderung': 40
        }
        
        for query, score in queries.items():
            self.redis_client.zadd(key, {query: score})
        
        # Get top 3
        top_3 = self.redis_client.zrevrange(key, 0, 2, withscores=True)
        
        assert len(top_3) == 3
        assert top_3[0][0] == 'persönliches budget'
        assert top_3[0][1] == 100
```

**Docker Compose for Integration Tests:**

```yaml
# docker-compose.test.yml

version: '3.8'

services:
  postgres-test:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: test_ios_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5433:5432"
    tmpfs:
      - /var/lib/postgresql/data

  elasticsearch-test:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms256m -Xmx256m"
    ports:
      - "9201:9200"
    tmpfs:
      - /usr/share/elasticsearch/data

  qdrant-test:
    image: qdrant/qdrant:v1.7.0
    ports:
      - "6334:6333"
    tmpfs:
      - /qdrant/storage

  redis-test:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    tmpfs:
      - /data

  app-test:
    build:
      context: .
      dockerfile: Dockerfile.test
    command: pytest tests/integration/ -v
    depends_on:
      - postgres-test
      - elasticsearch-test
      - qdrant-test
      - redis-test
    environment:
      - DATABASE_URL=postgresql://test_user:test_password@postgres-test:5432/test_ios_db
      - ELASTICSEARCH_URL=http://elasticsearch-test:9200
      - QDRANT_URL=http://qdrant-test:6333
      - REDIS_URL=redis://redis-test:6379/0
      - DJANGO_SETTINGS_MODULE=ios_core.settings.test
    volumes:
      - .:/app
      - test-results:/app/test-results

volumes:
  test-results:
```

**Run Integration Tests:**

```bash
#!/bin/bash
# scripts/run-integration-tests.sh

echo "Starting integration test environment..."

# Start services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 30

# Run tests
docker-compose -f docker-compose.test.yml run --rm app-test

# Capture exit code
TEST_EXIT_CODE=$?

# Cleanup
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

exit $TEST_EXIT_CODE
```

**Checklist:**
- [ ] Create integration test suite
- [ ] Setup test infrastructure (Docker Compose)
- [ ] Test PostgreSQL operations
- [ ] Test Elasticsearch integration
- [ ] Test Qdrant integration
- [ ] Test Redis caching
- [ ] Test cross-service integration
- [ ] Automate integration tests in CI

---

### Sprint 3-4: Core Search Implementation (Weeks 3-5)

#### Task 3.1: Elasticsearch Service Implementation
**Assignee:** Backend Developer
**Time:** 3 days
**Priority:** Critical

```python
# search/services/elasticsearch_service.py

"""
Elasticsearch service for full-text search
"""

from elasticsearch import Elasticsearch, NotFoundError
from django.conf import settings
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ElasticsearchService:
    """
    Service for Elasticsearch operations
    """
    
    def __init__(self):
        """Initialize Elasticsearch client"""
        self.client = Elasticsearch(
            settings.ELASTICSEARCH_DSL['default']['hosts'],
            timeout=settings.ELASTICSEARCH_DSL['default'].get('timeout', 30),
            max_retries=settings.ELASTICSEARCH_DSL['default'].get('max_retries', 3),
            retry_on_timeout=True
        )
        self.index_name = settings.SEARCH_CONFIG['elasticsearch']['index_name']
    
    def create_index(self, force: bool = False):
        """
        Create Elasticsearch index with proper mapping
        
        Args:
            force: Force recreate if index exists
        """
        if force and self.client.indices.exists(index=self.index_name):
            logger.warning(f"Deleting existing index: {self.index_name}")
            self.client.indices.delete(index=self.index_name)
        
        if self.client.indices.exists(index=self.index_name):
            logger.info(f"Index already exists: {self.index_name}")
            return
        
        mapping = {
            'settings': {
                'number_of_shards': 3,
                'number_of_replicas': 1,
                'analysis': {
                    'analyzer': {
                        'german_analyzer': {
                            'type': 'custom',
                            'tokenizer': 'standard',
                            'filter': [
                                'lowercase',
                                'german_stop',
                                'german_stemmer',
                                'german_normalization'
                            ]
                        },
                        'german_exact': {
                            'type': 'custom',
                            'tokenizer': 'standard',
                            'filter': ['lowercase']
                        }
                    },
                    'filter': {
                        'german_stop': {
                            'type': 'stop',
                            'stopwords': '_german_'
                        },
                        'german_stemmer': {
                            'type': 'stemmer',
                            'language': 'german'
                        },
                        'german_normalization': {
                            'type': 'german_normalization'
                        }
                    }
                }
            },
            'mappings': {
                'properties': {
                    'title': {
                        'type': 'text',
                        'analyzer': 'german_analyzer',
                        'fields': {
                            'exact': {
                                'type': 'text',
                                'analyzer': 'german_exact'
                            },
                            'keyword': {
                                'type': 'keyword'
                            }
                        }
                    },
                    'content': {
                        'type': 'text',
                        'analyzer': 'german_analyzer'
                    },
                    'summary': {
                        'type': 'text',
                        'analyzer': 'german_analyzer'
                    },
                    'document_type': {
                        'type': 'keyword'
                    },
                    'category': {
                        'type': 'keyword'
                    },
                    'legal_code': {
                        'type': 'keyword'
                    },
                    'paragraph': {
                        'type': 'keyword'
                    },
                    'tags': {
                        'type': 'keyword'
                    },
                    'created_at': {
                        'type': 'date'
                    },
                    'updated_at': {
                        'type': 'date'
                    },
                    'published_at': {
                        'type': 'date'
                    },
                    'is_active': {
                        'type': 'boolean'
                    },
                    'view_count': {
                        'type': 'integer'
                    },
                    'click_count': {
                        'type': 'integer'
                    }
                }
            }
        }
        
        self.client.indices.create(index=self.index_name, body=mapping)
        logger.info(f"Created index: {self.index_name}")
    
    def index_document(self, document) -> bool:
        """
        Index a single document
        
        Args:
            document: Document model instance
        
        Returns:
            Success status
        """
        try:
            doc_dict = {
                'title': document.title,
                'content': document.content,
                'summary': document.summary,
                'document_type': document.document_type,
                'category': document.category,
                'legal_code': document.legal_code,
                'paragraph': document.paragraph,
                'tags': document.tags,
                'created_at': document.created_at.isoformat(),
                'updated_at': document.updated_at.isoformat(),
                'is_active': document.is_active,
                'view_count': document.view_count,
                'click_count': document.click_count
            }
            
            if document.published_at:
                doc_dict['published_at'] = document.published_at.isoformat()
            
            result = self.client.index(
                index=self.index_name,
                id=str(document.id),
                document=doc_dict
            )
            
            logger.debug(f"Indexed document: {document.id}")
            return result['result'] in ['created', 'updated']
        
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            return False
    
    def bulk_index_documents(self, documents: List) -> Dict[str, int]:
        """
        Bulk index documents
        
        Args:
            documents: List of Document model instances
        
        Returns:
            Statistics dict
        """
        from elasticsearch.helpers import bulk
        
        actions = []
        for doc in documents:
            action = {
                '_index': self.index_name,
                '_id': str(doc.id),
                '_source': {
                    'title': doc.title,
                    'content': doc.content,
                    'summary': doc.summary,
                    'document_type': doc.document_type,
                    'category': doc.category,
                    'legal_code': doc.legal_code,
                    'paragraph': doc.paragraph,
                    'tags': doc.tags,
                    'created_at': doc.created_at.isoformat(),
                    'updated_at': doc.updated_at.isoformat(),
                    'is_active': doc.is_active,
                    'view_count': doc.view_count,
                    'click_count': doc.click_count
                }
            }
            
            if doc.published_at:
                action['_source']['published_at'] = doc.published_at.isoformat()
            
            actions.append(action)
        
        success, failed = bulk(self.client, actions, raise_on_error=False)
        
        logger.info(f"Bulk indexed {success} documents, {failed} failed")
        
        return {
            'success': success,
            'failed': failed,
            'total': len(documents)
        }
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'relevance'
    ) -> Dict:
        """
        Search documents
        
        Args:
            query: Search query
            filters: Optional filters dict
            page: Page number
            page_size: Results per page
            sort_by: Sort option
        
        Returns:
            Search results dict
        """
        from_offset = (page - 1) * page_size
        
        # Build query
        search_query = {
            'bool': {
                'must': [],
                'filter': []
            }
        }
        
        # Add text search
        if query:
            search_query['bool']['must'].append({
                'multi_match': {
                    'query': query,
                    'fields': [
                        'title^3',
                        'title.exact^2',
                        'summary^2',
                        'content',
                        'legal_code^2',
                        'paragraph^2'
                    ],
                    'type': 'best_fields',
                    'tie_breaker': 0.3,
                    'minimum_should_match': '75%'
                }
            })
        else:
            search_query['bool']['must'].append({'match_all': {}})
        
        # Add filters
        if filters:
            if 'document_type' in filters:
                search_query['bool']['filter'].append({
                    'term': {'document_type': filters['document_type']}
                })
            
            if 'category' in filters:
                search_query['bool']['filter'].append({
                    'term': {'category': filters['category']}
                })
            
            if 'legal_code' in filters:
                search_query['bool']['filter'].append({
                    'term': {'legal_code': filters['legal_code']}
                })
            
            if 'tags' in filters:
                search_query['bool']['filter'].append({
                    'terms': {'tags': filters['tags']}
                })
        
        # Always filter active documents
        search_query['bool']['filter'].append({
            'term': {'is_active': True}
        })
        
        # Build sort
        sort = self._build_sort(sort_by)
        
        # Execute search
        try:
            result = self.client.search(
                index=self.index_name,
                body={
                    'query': search_query,
                    'from': from_offset,
                    'size': page_size,
                    'sort': sort,
                    '_source': True
                }
            )
            
            hits = result['hits']['hits']
            total = result['hits']['total']['value']
            
            # Format results
            results = []
            for hit in hits:
                results.append({
                    'id': hit['_id'],
                    'score': hit['_score'],
                    'source': hit['_source']
                })
            
            return {
                'results': results,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                'results': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
                'error': str(e)
            }
    
    def _build_sort(self, sort_by: str) -> List:
        """Build sort configuration"""
        sort_options = {
            'relevance': ['_score'],
            'date_desc': [{'created_at': 'desc'}, '_score'],
            'date_asc': [{'created_at': 'asc'}, '_score'],
            'title': [{'title.keyword': 'asc'}, '_score'],
            'popularity': [{'click_count': 'desc'}, {'view_count': 'desc'}, '_score']
        }
        
        return sort_options.get(sort_by, ['_score'])
    
    def delete_document(self, document_id: str) -> bool:
        """Delete document from index"""
        try:
            self.client.delete(index=self.index_name, id=document_id)
            logger.debug(f"Deleted document from index: {document_id}")
            return True
        except NotFoundError:
            logger.warning(f"Document not found in index: {document_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
```

**Продолжить с Task 3.2: Qdrant Service Implementation?**