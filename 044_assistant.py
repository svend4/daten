Продолжаем реализацию Week 17-18. Теперь переходим к Day 115-116: Elasticsearch Migration для улучшения масштабируемости поиска.# 🚀 DAY 115-116: ELASTICSEARCH MIGRATION

---

## 📊 ЦЕЛЬ

Мигрировать с Whoosh на Elasticsearch для:
- Горизонтальная масштабируемость
- Производительность на больших объемах (>1M документов)
- Advanced search features (facets, aggregations, neural search)
- Better relevance scoring

---

## ФАЙЛ 55: `docker-compose.elasticsearch.yml`

```yaml
version: '3.8'

services:
  # ========================================================================
  # Elasticsearch Cluster (3 nodes)
  # ========================================================================
  es01:
    image: elasticsearch:8.11.3
    container_name: ios-es01
    restart: unless-stopped
    
    environment:
      - node.name=es01
      - cluster.name=ios-es-cluster
      - discovery.seed_hosts=es02,es03
      - cluster.initial_master_nodes=es01,es02,es03
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - xpack.security.enrollment.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    
    volumes:
      - es01-data:/usr/share/elasticsearch/data
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
      - ./elasticsearch/config/synonyms.txt:/usr/share/elasticsearch/config/synonyms.txt:ro
    
    ports:
      - "9200:9200"
      - "9300:9300"
    
    networks:
      - ios-network
    
    healthcheck:
      test: ["CMD-SHELL", "curl -f -u elastic:${ELASTIC_PASSWORD} http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  es02:
    image: elasticsearch:8.11.3
    container_name: ios-es02
    restart: unless-stopped
    
    environment:
      - node.name=es02
      - cluster.name=ios-es-cluster
      - discovery.seed_hosts=es01,es03
      - cluster.initial_master_nodes=es01,es02,es03
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    
    ulimits:
      memlock:
        soft: -1
        hard: -1
    
    volumes:
      - es02-data:/usr/share/elasticsearch/data
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    
    networks:
      - ios-network
    
    depends_on:
      - es01

  es03:
    image: elasticsearch:8.11.3
    container_name: ios-es03
    restart: unless-stopped
    
    environment:
      - node.name=es03
      - cluster.name=ios-es-cluster
      - discovery.seed_hosts=es01,es02
      - cluster.initial_master_nodes=es01,es02,es03
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
    
    ulimits:
      memlock:
        soft: -1
        hard: -1
    
    volumes:
      - es03-data:/usr/share/elasticsearch/data
      - ./elasticsearch/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
    
    networks:
      - ios-network
    
    depends_on:
      - es01

volumes:
  es01-data:
    driver: local
  es02-data:
    driver: local
  es03-data:
    driver: local

networks:
  ios-network:
    external: true
```

---

## ФАЙЛ 56: `elasticsearch/config/elasticsearch.yml`

```yaml
# Elasticsearch Configuration

cluster.name: ios-es-cluster

# Network
network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# Discovery
discovery.type: multi-node

# Paths
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs

# Memory
bootstrap.memory_lock: true

# Security
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.verification_mode: certificate

# Monitoring
xpack.monitoring.collection.enabled: true

# Index settings
action.auto_create_index: true
action.destructive_requires_name: true

# Thread pool
thread_pool.write.queue_size: 1000
thread_pool.search.queue_size: 1000

# Circuit breakers
indices.breaker.total.limit: 70%
indices.breaker.request.limit: 40%
```

---

## ФАЙЛ 57: `elasticsearch/config/synonyms.txt`

```text
# German Legal Synonyms for IOS System

# SGB Variations
sgb, sozialgesetzbuch
sgb ix, sgb 9, sozialgesetzbuch neuntes buch
sgb xii, sgb 12, sozialgesetzbuch zwölftes buch

# Document Types
widerspruch, beschwerde, einspruch
antrag, gesuch, beantragung
bescheid, entscheidung, verfügung
urteil, entscheidung, richterspruch

# Common Terms
persönliches budget, pb, persönliche budget
eingliederungshilfe, teilhabeleistung
teilhabe, partizipation
behinderung, handicap
schwerbehinderung, schwerbehindert

# Organizations
bezirk, landkreis
sozialamt, amt für soziales
versorgungsamt, amt für versorgung
```

---

## ФАЙЛ 58: `ios_core/search/elasticsearch_service.py`

```python
"""
Elasticsearch-based search service
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio

from elasticsearch import AsyncElasticsearch, NotFoundError, RequestError
from elasticsearch.helpers import async_bulk

from ..config import settings
from ..models import DocumentModel, EntityModel
from .base import SearchResult

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """
    Advanced search with Elasticsearch
    
    Features:
    - Full-text search with BM25
    - Semantic search with embeddings
    - Faceted search
    - Aggregations
    - Highlighting
    - Fuzzy matching
    - Synonym support
    """
    
    # Index settings
    INDEX_SETTINGS = {
        "number_of_shards": 3,
        "number_of_replicas": 2,
        "refresh_interval": "5s",
        "max_result_window": 10000,
        "analysis": {
            "filter": {
                "german_stop": {
                    "type": "stop",
                    "stopwords": "_german_"
                },
                "german_stemmer": {
                    "type": "stemmer",
                    "language": "german"
                },
                "german_synonym": {
                    "type": "synonym",
                    "synonyms_path": "synonyms.txt"
                }
            },
            "analyzer": {
                "german_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": [
                        "lowercase",
                        "german_stop",
                        "german_synonym",
                        "german_stemmer"
                    ]
                }
            }
        }
    }
    
    # Index mapping
    INDEX_MAPPING = {
        "properties": {
            "id": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "german_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "exact": {"type": "text", "analyzer": "standard"}
                }
            },
            "content": {
                "type": "text",
                "analyzer": "german_analyzer"
            },
            "document_type": {"type": "keyword"},
            "category": {"type": "keyword"},
            "domain_name": {"type": "keyword"},
            "author": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "file_path": {"type": "keyword", "index": False},
            "file_size": {"type": "long"},
            "classification_confidence": {"type": "float"},
            "entities": {
                "type": "nested",
                "properties": {
                    "type": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "german_analyzer"},
                    "confidence": {"type": "float"}
                }
            },
            "relations": {
                "type": "nested",
                "properties": {
                    "type": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "target": {"type": "keyword"}
                }
            },
            # Vector field for neural search
            "embedding": {
                "type": "dense_vector",
                "dims": 768,
                "index": True,
                "similarity": "cosine"
            }
        }
    }
    
    def __init__(self):
        self.client = None
        self.index_name = "ios-documents"
    
    async def initialize(self):
        """Initialize Elasticsearch client"""
        
        self.client = AsyncElasticsearch(
            hosts=[settings.elasticsearch_url],
            basic_auth=("elastic", settings.elasticsearch_password),
            verify_certs=False,  # For development
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # Create index if not exists
        await self._ensure_index()
        
        logger.info(f"Elasticsearch initialized: {settings.elasticsearch_url}")
    
    async def close(self):
        """Close Elasticsearch client"""
        if self.client:
            await self.client.close()
    
    async def _ensure_index(self):
        """Ensure index exists with correct mapping"""
        
        try:
            exists = await self.client.indices.exists(index=self.index_name)
            
            if not exists:
                await self.client.indices.create(
                    index=self.index_name,
                    settings=self.INDEX_SETTINGS,
                    mappings=self.INDEX_MAPPING
                )
                logger.info(f"Created index: {self.index_name}")
            else:
                logger.info(f"Index already exists: {self.index_name}")
                
        except RequestError as e:
            logger.error(f"Error creating index: {e}")
            raise
    
    async def index_document(
        self,
        document: DocumentModel,
        entities: List[EntityModel] = None,
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Index a document
        
        Args:
            document: Document to index
            entities: List of entities
            embedding: Vector embedding for neural search
        
        Returns:
            Success status
        """
        
        try:
            # Prepare document
            doc = {
                "id": document.id,
                "title": document.title,
                "content": document.content or "",
                "document_type": document.document_type,
                "category": document.category,
                "domain_name": document.domain_name,
                "author": document.author,
                "tags": document.tags or [],
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
                "file_path": str(document.file_path),
                "file_size": document.file_size,
                "classification_confidence": document.classification_confidence,
            }
            
            # Add entities
            if entities:
                doc["entities"] = [
                    {
                        "type": e.type,
                        "name": e.name,
                        "confidence": e.confidence
                    }
                    for e in entities
                ]
            
            # Add embedding
            if embedding:
                doc["embedding"] = embedding
            
            # Index
            response = await self.client.index(
                index=self.index_name,
                id=document.id,
                document=doc
            )
            
            logger.debug(f"Indexed document: {document.id}")
            return response["result"] in ["created", "updated"]
            
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            return False
    
    async def bulk_index(
        self,
        documents: List[DocumentModel],
        batch_size: int = 500
    ) -> Dict[str, int]:
        """
        Bulk index documents
        
        Args:
            documents: List of documents to index
            batch_size: Batch size for bulk indexing
        
        Returns:
            Statistics (success, failed)
        """
        
        stats = {"success": 0, "failed": 0}
        
        def generate_actions():
            for doc in documents:
                yield {
                    "_index": self.index_name,
                    "_id": doc.id,
                    "_source": {
                        "id": doc.id,
                        "title": doc.title,
                        "content": doc.content or "",
                        "document_type": doc.document_type,
                        "category": doc.category,
                        "domain_name": doc.domain_name,
                        "author": doc.author,
                        "tags": doc.tags or [],
                        "created_at": doc.created_at.isoformat(),
                        "updated_at": doc.updated_at.isoformat(),
                        "file_path": str(doc.file_path),
                        "file_size": doc.file_size,
                        "classification_confidence": doc.classification_confidence,
                    }
                }
        
        try:
            async for ok, response in async_bulk(
                self.client,
                generate_actions(),
                chunk_size=batch_size,
                raise_on_error=False
            ):
                if ok:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    logger.warning(f"Failed to index: {response}")
            
            logger.info(f"Bulk indexing complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in bulk indexing: {e}")
            return stats
    
    async def search(
        self,
        query: str,
        domain_name: Optional[str] = None,
        document_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        offset: int = 0,
        search_type: str = "bm25"
    ) -> Dict[str, Any]:
        """
        Search documents
        
        Args:
            query: Search query
            domain_name: Filter by domain
            document_type: Filter by type
            date_from: Filter by date (from)
            date_to: Filter by date (to)
            tags: Filter by tags
            limit: Max results
            offset: Offset for pagination
            search_type: Type of search (bm25, semantic, hybrid)
        
        Returns:
            Search results with metadata
        """
        
        # Build query
        if search_type == "bm25":
            query_body = self._build_bm25_query(query)
        elif search_type == "semantic":
            query_body = await self._build_semantic_query(query)
        elif search_type == "hybrid":
            query_body = await self._build_hybrid_query(query)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
        
        # Add filters
        filters = self._build_filters(
            domain_name=domain_name,
            document_type=document_type,
            date_from=date_from,
            date_to=date_to,
            tags=tags
        )
        
        if filters:
            query_body = {
                "bool": {
                    "must": query_body,
                    "filter": filters
                }
            }
        
        # Search
        try:
            response = await self.client.search(
                index=self.index_name,
                query=query_body,
                size=limit,
                from_=offset,
                highlight={
                    "fields": {
                        "title": {"number_of_fragments": 0},
                        "content": {"fragment_size": 150, "number_of_fragments": 3}
                    }
                },
                _source_excludes=["embedding"]  # Don't return embeddings
            )
            
            # Format results
            results = self._format_search_results(response)
            
            return {
                "results": results,
                "total": response["hits"]["total"]["value"],
                "took": response["took"],
                "max_score": response["hits"]["max_score"]
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "results": [],
                "total": 0,
                "took": 0,
                "max_score": 0
            }
    
    def _build_bm25_query(self, query: str) -> Dict:
        """Build BM25 query"""
        
        return {
            "multi_match": {
                "query": query,
                "fields": [
                    "title^3",
                    "content",
                    "entities.name^2"
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "or",
                "minimum_should_match": "75%"
            }
        }
    
    async def _build_semantic_query(self, query: str) -> Dict:
        """Build semantic search query with kNN"""
        
        # Get query embedding
        embedding = await self._get_embedding(query)
        
        return {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                    "params": {"query_vector": embedding}
                }
            }
        }
    
    async def _build_hybrid_query(self, query: str) -> Dict:
        """Build hybrid query (BM25 + semantic)"""
        
        # Get query embedding
        embedding = await self._get_embedding(query)
        
        return {
            "bool": {
                "should": [
                    # BM25 component (60% weight)
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content", "entities.name^2"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "boost": 0.6
                        }
                    },
                    # Semantic component (40% weight)
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                                "params": {"query_vector": embedding}
                            },
                            "boost": 0.4
                        }
                    }
                ]
            }
        }
    
    def _build_filters(
        self,
        domain_name: Optional[str] = None,
        document_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """Build filter clauses"""
        
        filters = []
        
        if domain_name:
            filters.append({"term": {"domain_name": domain_name}})
        
        if document_type:
            filters.append({"term": {"document_type": document_type}})
        
        if date_from or date_to:
            date_filter = {"range": {"created_at": {}}}
            if date_from:
                date_filter["range"]["created_at"]["gte"] = date_from.isoformat()
            if date_to:
                date_filter["range"]["created_at"]["lte"] = date_to.isoformat()
            filters.append(date_filter)
        
        if tags:
            filters.append({"terms": {"tags": tags}})
        
        return filters
    
    def _format_search_results(self, response: Dict) -> List[Dict]:
        """Format Elasticsearch response"""
        
        results = []
        
        for hit in response["hits"]["hits"]:
            result = {
                "id": hit["_id"],
                "score": hit["_score"],
                **hit["_source"]
            }
            
            # Add highlights
            if "highlight" in hit:
                highlights = []
                for field, fragments in hit["highlight"].items():
                    highlights.extend(fragments)
                result["highlights"] = highlights
            
            results.append(result)
        
        return results
    
    async def aggregate(
        self,
        field: str,
        query: Optional[str] = None,
        filters: Optional[Dict] = None,
        size: int = 100
    ) -> List[Dict]:
        """
        Aggregate documents by field
        
        Args:
            field: Field to aggregate on
            query: Optional search query
            filters: Optional filters
            size: Max aggregation buckets
        
        Returns:
            Aggregation results
        """
        
        # Build query
        query_body = {"match_all": {}}
        if query:
            query_body = self._build_bm25_query(query)
        
        # Build aggregation
        agg_body = {
            "size": 0,
            "query": query_body,
            "aggs": {
                "by_field": {
                    "terms": {
                        "field": field,
                        "size": size
                    }
                }
            }
        }
        
        # Execute
        response = await self.client.search(
            index=self.index_name,
            body=agg_body
        )
        
        # Format results
        buckets = response["aggregations"]["by_field"]["buckets"]
        
        return [
            {
                "key": bucket["key"],
                "count": bucket["doc_count"]
            }
            for bucket in buckets
        ]
    
    async def suggest(
        self,
        prefix: str,
        field: str = "title",
        size: int = 10
    ) -> List[str]:
        """
        Get search suggestions
        
        Args:
            prefix: Prefix to match
            field: Field to suggest from
            size: Max suggestions
        
        Returns:
            List of suggestions
        """
        
        response = await self.client.search(
            index=self.index_name,
            suggest={
                "suggestions": {
                    "prefix": prefix,
                    "completion": {
                        "field": f"{field}.suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            }
        )
        
        options = response["suggest"]["suggestions"][0]["options"]
        return [opt["text"] for opt in options]
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from index"""
        
        try:
            await self.client.delete(
                index=self.index_name,
                id=document_id
            )
            logger.debug(f"Deleted document: {document_id}")
            return True
            
        except NotFoundError:
            logger.warning(f"Document not found: {document_id}")
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def reindex_all(self, documents: List[DocumentModel]) -> Dict:
        """Reindex all documents"""
        
        logger.info(f"Starting reindex of {len(documents)} documents")
        
        # Delete existing index
        try:
            await self.client.indices.delete(index=self.index_name)
            logger.info(f"Deleted index: {self.index_name}")
        except NotFoundError:
            pass
        
        # Recreate index
        await self._ensure_index()
        
        # Bulk index
        stats = await self.bulk_index(documents)
        
        # Refresh index
        await self.client.indices.refresh(index=self.index_name)
        
        logger.info(f"Reindex complete: {stats}")
        return stats
    
    async def _get_embedding(self, text: str) -> List[float]:
        """
        Get text embedding for semantic search
        
        TODO: Integrate with actual embedding model (BERT, etc.)
        For now, returns dummy embedding
        """
        # Placeholder - will be implemented in Week 23-24
        import random
        return [random.random() for _ in range(768)]
    
    async def get_cluster_health(self) -> Dict:
        """Get Elasticsearch cluster health"""
        
        return await self.client.cluster.health()
    
    async def get_index_stats(self) -> Dict:
        """Get index statistics"""
        
        stats = await self.client.indices.stats(index=self.index_name)
        
        return {
            "total_docs": stats["_all"]["primaries"]["docs"]["count"],
            "total_size_bytes": stats["_all"]["primaries"]["store"]["size_in_bytes"],
            "shards": stats["_shards"]
        }
```

---

## ФАЙЛ 59: `ios_core/search/migration.py`

```python
"""
Migration from Whoosh to Elasticsearch
"""

import logging
from typing import List
from pathlib import Path
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import DocumentModel, EntityModel
from .elasticsearch_service import ElasticsearchService
from ..database import async_session

logger = logging.getLogger(__name__)


class SearchMigration:
    """Migrate search from Whoosh to Elasticsearch"""
    
    def __init__(self, es_service: ElasticsearchService):
        self.es = es_service
    
    async def migrate_all(self, batch_size: int = 500) -> Dict:
        """
        Migrate all documents from database to Elasticsearch
        
        Args:
            batch_size: Documents per batch
        
        Returns:
            Migration statistics
        """
        
        logger.info("Starting search migration to Elasticsearch")
        
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "batches": 0
        }
        
        async with async_session() as session:
            # Count total documents
            result = await session.execute(
                select(func.count(DocumentModel.id))
            )
            total = result.scalar_one()
            stats["total"] = total
            
            logger.info(f"Migrating {total} documents")
            
            # Migrate in batches
            offset = 0
            while offset < total:
                # Fetch batch
                result = await session.execute(
                    select(DocumentModel)
                    .limit(batch_size)
                    .offset(offset)
                )
                documents = result.scalars().all()
                
                if not documents:
                    break
                
                # Index batch
                batch_stats = await self.es.bulk_index(documents, batch_size)
                
                stats["success"] += batch_stats["success"]
                stats["failed"] += batch_stats["failed"]
                stats["batches"] += 1
                
                offset += batch_size
                
                logger.info(
                    f"Progress: {offset}/{total} "
                    f"({offset/total*100:.1f}%)"
                )
                
                # Small delay to avoid overwhelming ES
                await asyncio.sleep(0.1)
        
        # Refresh index
        await self.es.client.indices.refresh(index=self.es.index_name)
        
        logger.info(f"Migration complete: {stats}")
        return stats
    
    async def verify_migration(self) -> Dict:
        """
        Verify migration was successful
        
        Returns:
            Verification results
        """
        
        logger.info("Verifying migration")
        
        results = {
            "database_count": 0,
            "elasticsearch_count": 0,
            "match": False,
            "sample_checks": []
        }
        
        async with async_session() as session:
            # Count in database
            result = await session.execute(
                select(func.count(DocumentModel.id))
            )
            db_count = result.scalar_one()
            results["database_count"] = db_count
            
            # Count in Elasticsearch
            es_stats = await self.es.get_index_stats()
            es_count = es_stats["total_docs"]
            results["elasticsearch_count"] = es_count
            
            # Check if counts match
            results["match"] = (db_count == es_count)
            
            # Sample random documents
            result = await session.execute(
                select(DocumentModel)
                .order_by(func.random())
                .limit(10)
            )
            sample_docs = result.scalars().all()
            
            # Verify each sample in ES
            for doc in sample_docs:
                try:
                    es_doc = await self.es.client.get(
                        index=self.es.index_name,
                        id=doc.id
                    )
                    
                    check = {
                        "id": doc.id,
                        "found": True,
                        "title_match": es_doc["_source"]["title"] == doc.title
                    }
                except:
                    check = {
                        "id": doc.id,
                        "found": False,
                        "title_match": False
                    }
                
                results["sample_checks"].append(check)
        
        # Log results
        logger.info(f"Verification results: {results}")
        
        if results["match"]:
            logger.info("✓ Migration verified successfully")
        else:
            logger.warning("✗ Migration verification failed")
        
        return results
    
    async def rollback(self):
        """Rollback migration (delete ES index)"""
        
        logger.warning("Rolling back migration")
        
        try:
            await self.es.client.indices.delete(index=self.es.index_name)
            logger.info(f"Deleted index: {self.es.index_name}")
        except Exception as e:
            logger.error(f"Rollback error: {e}")
```

---

## ФАЙЛ 60: `scripts/migrate_to_elasticsearch.py`

```python
"""
Migration script: Whoosh → Elasticsearch
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.search.migration import SearchMigration
from ios_core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Run migration"""
    
    print("="*80)
    print("ELASTICSEARCH MIGRATION")
    print("="*80)
    print()
    
    # Initialize Elasticsearch
    logger.info("Initializing Elasticsearch...")
    es = ElasticsearchService()
    await es.initialize()
    
    # Check cluster health
    health = await es.get_cluster_health()
    logger.info(f"Cluster health: {health['status']}")
    
    if health['status'] == 'red':
        logger.error("Cluster is unhealthy, aborting migration")
        return 1
    
    # Initialize migration
    migration = SearchMigration(es)
    
    # Confirm migration
    print()
    print("This will migrate all documents from Whoosh to Elasticsearch.")
    print("The Whoosh index will NOT be deleted (for rollback).")
    print()
    confirm = input("Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Migration cancelled")
        return 0
    
    print()
    
    # Run migration
    logger.info("Starting migration...")
    stats = await migration.migrate_all(batch_size=500)
    
    print()
    print("="*80)
    print("MIGRATION COMPLETE")
    print("="*80)
    print(f"Total documents: {stats['total']}")
    print(f"Successfully indexed: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Batches processed: {stats['batches']}")
    print()
    
    # Verify migration
    logger.info("Verifying migration...")
    verification = await migration.verify_migration()
    
    print()
    print("="*80)
    print("VERIFICATION")
    print("="*80)
    print(f"Database count: {verification['database_count']}")
    print(f"Elasticsearch count: {verification['elasticsearch_count']}")
    print(f"Match: {'✓ Yes' if verification['match'] else '✗ No'}")
    print()
    
    # Sample checks
    print("Sample checks:")
    for check in verification['sample_checks']:
        status = "✓" if check['found'] and check['title_match'] else "✗"
        print(f"  {status} {check['id']}")
    
    print()
    
    # Index statistics
    index_stats = await es.get_index_stats()
    print("="*80)
    print("INDEX STATISTICS")
    print("="*80)
    print(f"Total documents: {index_stats['total_docs']}")
    print(f"Total size: {index_stats['total_size_bytes'] / 1024 / 1024:.2f} MB")
    print(f"Shards: {index_stats['shards']}")
    print()
    
    # Close ES connection
    await es.close()
    
    if verification['match']:
        print("✓ Migration successful!")
        print()
        print("Next steps:")
        print("1. Update application config to use Elasticsearch")
        print("2. Test search functionality")
        print("3. Monitor performance")
        print("4. After verification, Whoosh index can be deleted")
        return 0
    else:
        print("✗ Migration verification failed!")
        print()
        print("Run rollback:")
        print("  python scripts/rollback_elasticsearch.py")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
```

---

## ФАЙЛ 61: `tests/search/test_elasticsearch.py`

```python
"""
Tests for Elasticsearch service
"""

import pytest
from datetime import datetime

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.models import DocumentModel


@pytest.fixture
async def es_service():
    """Elasticsearch service fixture"""
    
    es = ElasticsearchService()
    await es.initialize()
    
    yield es
    
    # Cleanup
    await es.client.indices.delete(index=es.index_name, ignore=[404])
    await es.close()


@pytest.mark.asyncio
async def test_index_document(es_service, sample_document):
    """Test document indexing"""
    
    success = await es_service.index_document(sample_document)
    
    assert success
    
    # Verify document is indexed
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    response = await es_service.client.get(
        index=es_service.index_name,
        id=sample_document.id
    )
    
    assert response["_source"]["title"] == sample_document.title


@pytest.mark.asyncio
async def test_bm25_search(es_service, sample_documents):
    """Test BM25 search"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Search
    results = await es_service.search(
        query="Widerspruch",
        search_type="bm25",
        limit=10
    )
    
    assert results["total"] > 0
    assert len(results["results"]) > 0
    assert results["results"][0]["score"] > 0


@pytest.mark.asyncio
async def test_filtered_search(es_service, sample_documents):
    """Test search with filters"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Search with domain filter
    results = await es_service.search(
        query="test",
        domain_name="SGB-IX",
        search_type="bm25"
    )
    
    assert all(r["domain_name"] == "SGB-IX" for r in results["results"])


@pytest.mark.asyncio
async def test_aggregation(es_service, sample_documents):
    """Test aggregations"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Aggregate by document type
    agg_results = await es_service.aggregate(field="document_type")
    
    assert len(agg_results) > 0
    assert all("key" in r and "count" in r for r in agg_results)


@pytest.mark.asyncio
async def test_bulk_index(es_service, sample_documents):
    """Test bulk indexing"""
    
    stats = await es_service.bulk_index(sample_documents)
    
    assert stats["success"] == len(sample_documents)
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_document(es_service, sample_document):
    """Test document deletion"""
    
    # Index document
    await es_service.index_document(sample_document)
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Delete
    success = await es_service.delete_document(sample_document.id)
    
    assert success
    
    # Verify deleted
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    from elasticsearch import NotFoundError
    with pytest.raises(NotFoundError):
        await es_service.client.get(
            index=es_service.index_name,
            id=sample_document.id
        )
```

---

## ФАЙЛ 62: `scripts/benchmark_search.py`

```python
"""
Benchmark search performance: Whoosh vs Elasticsearch
"""

import asyncio
import time
import statistics
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.services.search import SearchService  # Old Whoosh service


async def benchmark_search_engine(
    service,
    queries: List[str],
    iterations: int = 10
) -> dict:
    """Benchmark search service"""
    
    results = {
        "queries": len(queries),
        "iterations": iterations,
        "times": [],
        "avg_time": 0,
        "median_time": 0,
        "min_time": 0,
        "max_time": 0,
        "p95_time": 0
    }
    
    # Warm up
    for query in queries[:5]:
        await service.search(query, limit=10)
    
    # Benchmark
    for _ in range(iterations):
        for query in queries:
            start = time.time()
            await service.search(query, limit=10)
            duration = (time.time() - start) * 1000  # ms
            results["times"].append(duration)
    
    # Calculate statistics
    times = results["times"]
    results["avg_time"] = statistics.mean(times)
    results["median_time"] = statistics.median(times)
    results["min_time"] = min(times)
    results["max_time"] = max(times)
    results["p95_time"] = statistics.quantiles(times, n=20)[18]  # 95th percentile
    
    return results


async def main():
    """Run benchmark"""
    
    print("="*80)
    print("SEARCH PERFORMANCE BENCHMARK")
    print("="*80)
    print()
    
    # Test queries
    queries = [
        "Persönliches Budget",
        "Widerspruch Bescheid",
        "§29 SGB IX",
        "Eingliederungshilfe",
        "Bezirk Oberbayern",
        "Schwerbehinderung",
        "Teilhabe Leistung",
        "Antrag Sozialamt",
        "Urteil Sozialgericht",
        "Beratung Hilfe"
    ]
    
    print(f"Test queries: {len(queries)}")
    print(f"Iterations: 10")
    print()
    
    # Benchmark Whoosh
    print("Benchmarking Whoosh...")
    whoosh_service = SearchService()
    whoosh_results = await benchmark_search_engine(whoosh_service, queries)
    
    print(f"  Avg: {whoosh_results['avg_time']:.2f}ms")
    print(f"  Median: {whoosh_results['median_time']:.2f}ms")
    print(f"  P95: {whoosh_results['p95_time']:.2f}ms")
    print()
    
    # Benchmark Elasticsearch
    print("Benchmarking Elasticsearch...")
    es_service = ElasticsearchService()
    await es_service.initialize()
    
    es_results = await benchmark_search_engine(es_service, queries)
    
    print(f"  Avg: {es_results['avg_time']:.2f}ms")
    print(f"  Median: {es_results['median_time']:.2f}ms")
    print(f"  P95: {es_results['p95_time']:.2f}ms")
    print()
    
    # Comparison
    print("="*80)
    print("COMPARISON")
    print("="*80)
    print()
    
    speedup_avg = whoosh_results['avg_time'] / es_results['avg_time']
    speedup_p95 = whoosh_results['p95_time'] / es_results['p95_time']
    
    print(f"Average time:")
    print(f"  Whoosh: {whoosh_results['avg_time']:.2f}ms")
    print(f"  Elasticsearch: {es_results['avg_time']:.2f}ms")
    print(f"  Speedup: {speedup_avg:.2f}x")
    print()
    
    print(f"P95 latency:")
    print(f"  Whoosh: {whoosh_results['p95_time']:.2f}ms")
    print(f"  Elasticsearch: {es_results['p95_time']:.2f}ms")
    print(f"  Speedup: {speedup_p95:.2f}x")
    print()
    
    # Winner
    if es_results['avg_time'] < whoosh_results['avg_time']:
        print("✓ Elasticsearch is faster!")
    else:
        print("✓ Whoosh is faster!")
    
    await es_service.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📋 ИНСТРУКЦИИ ПО РАЗВЕРТЫВАНИЮ

### Шаг 1: Подготовка

```bash
# Обновить requirements.txt
cat >> requirements.txt << 'EOF'

# Elasticsearch
elasticsearch[async]==8.11.3
EOF

# Установить
pip install -r requirements.txt

# Обновить .env
cat >> .env << 'EOF'

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_PASSWORD=changeme
ELASTIC_PASSWORD=changeme
EOF
```

### Шаг 2: Запуск Elasticsearch

```bash
# Создать директории
mkdir -p elasticsearch/config

# Копировать конфиги
cp elasticsearch/config/elasticsearch.yml elasticsearch/config/
cp elasticsearch/config/synonyms.txt elasticsearch/config/

# Запустить кластер
docker-compose -f docker-compose.elasticsearch.yml up -d

# Проверить статус
docker-compose -f docker-compose.elasticsearch.yml ps

# Проверить health
curl -u elastic:changeme http://localhost:9200/_cluster/health?pretty

# Expected: status "green" or "yellow"
```

### Шаг 3: Миграция данных

```bash
# Запустить миграцию
python scripts/migrate_to_elasticsearch.py

# Процесс:
# 1. Подтверждение
# 2. Миграция по батчам
# 3. Верификация
# 4. Статистика

# Expected output:
# ✓ Migration successful!
# Database count: 1000
# Elasticsearch count: 1000
# Match: ✓ Yes
```

### Шаг 4: Обновление приложения

```python
# Обновить ios_core/system.py

from .search.elasticsearch_service import ElasticsearchService

class IOSSystem:
    def __init__(self):
        # Replace Whoosh with Elasticsearch
        self.search_service = ElasticsearchService()
    
    async def initialize(self):
        await self.search_service.initialize()
```

### Шаг 5: Тестирование

```bash
# Запустить тесты
pytest tests/search/test_elasticsearch.py -v

# Benchmark
python scripts/benchmark_search.py

# Expected improvement:
# Elasticsearch 2-3x faster than Whoosh
# Better relevance
# More features
```

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После Day 115-116:

✅ **Elasticsearch Cluster**
- 3-node cluster running
- Green health status
- Sharding configured

✅ **Migration**
- All documents migrated
- Data verified
- No data loss

✅ **Performance**
- Search 2-3x faster
- Scales to 10M+ docs
- <200ms average latency

✅ **Features**
- Advanced search (BM25)
- Aggregations
- Faceted search
- Synonym support

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

**Day 117-118:** Security Enhancement (Audit Logging + 2FA)

**Готовы продолжить?**