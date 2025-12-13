Пользователь готов продолжить deep-dive в поисковую систему. Продолжу с детальным рассмотрением Elasticsearch implementation, затем Vector search, гибридный ранкинг и т.д.# 🎯 DEEP-DIVE: SEARCH SYSTEM (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 2: `docs/deep-dive/search/ELASTICSEARCH_IMPLEMENTATION.md`

```markdown
# Elasticsearch Implementation - Deep Dive

## 🔍 Index Architecture

### Document Schema

```json
{
  "mappings": {
    "properties": {
      "id": {
        "type": "keyword"
      },
      "title": {
        "type": "text",
        "analyzer": "ios_analyzer",
        "fields": {
          "keyword": {
            "type": "keyword"
          },
          "suggest": {
            "type": "completion",
            "analyzer": "simple"
          }
        },
        "boost": 2.0
      },
      "content": {
        "type": "text",
        "analyzer": "ios_analyzer",
        "term_vector": "with_positions_offsets",
        "store": true
      },
      "summary": {
        "type": "text",
        "analyzer": "ios_analyzer"
      },
      "tags": {
        "type": "keyword"
      },
      "document_type": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date",
        "format": "strict_date_optional_time||epoch_millis"
      },
      "updated_at": {
        "type": "date"
      },
      "owner_id": {
        "type": "keyword"
      },
      "owner_name": {
        "type": "text",
        "analyzer": "simple"
      },
      "permissions": {
        "type": "nested",
        "properties": {
          "user_id": {"type": "keyword"},
          "role": {"type": "keyword"},
          "access_level": {"type": "keyword"}
        }
      },
      "metadata": {
        "type": "object",
        "dynamic": true
      },
      "language": {
        "type": "keyword"
      },
      "view_count": {
        "type": "integer"
      },
      "download_count": {
        "type": "integer"
      },
      "relevance_score": {
        "type": "float"
      },
      "embedding_id": {
        "type": "keyword"
      },
      "file_size": {
        "type": "long"
      },
      "file_extension": {
        "type": "keyword"
      },
      "domain": {
        "type": "keyword"
      },
      "category": {
        "type": "keyword"
      },
      "status": {
        "type": "keyword"
      }
    }
  },
  "settings": {
    "number_of_shards": 5,
    "number_of_replicas": 2,
    "refresh_interval": "5s",
    "max_result_window": 10000,
    "analysis": {
      "analyzer": {
        "ios_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "ios_stop",
            "ios_synonym",
            "ios_stemmer",
            "asciifolding"
          ]
        },
        "ios_search_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": [
            "lowercase",
            "ios_stop",
            "ios_stemmer"
          ]
        }
      },
      "filter": {
        "ios_stop": {
          "type": "stop",
          "stopwords": ["_german_", "_english_", "_russian_"]
        },
        "ios_synonym": {
          "type": "synonym",
          "synonyms_path": "analysis/synonyms.txt"
        },
        "ios_stemmer": {
          "type": "stemmer",
          "language": "german"
        }
      }
    }
  }
}
```

### Custom Analyzers Explained

**1. IOS Analyzer (Indexing):**
```
Input: "Persönliches Budget für Assistenzleistungen"
  ↓ standard tokenizer
["Persönliches", "Budget", "für", "Assistenzleistungen"]
  ↓ lowercase
["persönliches", "budget", "für", "assistenzleistungen"]
  ↓ ios_stop (remove stopwords)
["persönliches", "budget", "assistenzleistungen"]
  ↓ ios_synonym (expand)
["persönliches", "personal", "budget", "haushalt", "assistenzleistungen", "hilfe"]
  ↓ ios_stemmer (German stemming)
["person", "person", "budget", "haushalt", "assistenz", "hilf"]
  ↓ asciifolding (normalize accents)
["person", "person", "budget", "haushalt", "assistenz", "hilf"]
```

**2. Search Analyzer (Querying):**
```
Input: "persönliches Budget"
  ↓ standard tokenizer
["persönliches", "Budget"]
  ↓ lowercase
["persönliches", "budget"]
  ↓ ios_stop
["persönliches", "budget"]
  ↓ ios_stemmer
["person", "budget"]
```

**Why Different Analyzers?**
- Index time: Expand with synonyms (broader matching)
- Search time: No synonyms (precise user intent)
- Result: Query "Budget" matches document with "Haushalt"

---

## 🔎 Search Implementation

### Elasticsearch Client

```python
# ios_core/search/elasticsearch_search.py

from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Individual search result"""
    document_id: int
    title: str
    summary: str
    score: float
    highlights: Dict[str, List[str]]
    metadata: Dict
    document_type: str
    
@dataclass
class SearchResponse:
    """Complete search response"""
    results: List[SearchResult]
    total_hits: int
    took_ms: int
    max_score: float
    aggregations: Optional[Dict] = None

class ElasticsearchSearchEngine:
    """
    Elasticsearch search implementation
    
    Features:
    - Multi-field search with boosting
    - Fuzzy matching
    - Phrase matching
    - Highlighting
    - Aggregations
    - Filtering
    - Pagination
    """
    
    def __init__(self, es_client: Elasticsearch, index_name: str = "documents"):
        self.es = es_client
        self.index_name = index_name
    
    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 10,
        boost_fields: Optional[Dict[str, float]] = None,
        user_id: Optional[int] = None,
        fuzzy: bool = False,
        highlight: bool = True,
        aggregations: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        Execute search query
        
        Args:
            query: Search query string
            filters: Structured filters (date, type, etc)
            page: Page number (1-indexed)
            page_size: Results per page
            boost_fields: Field boost values
            user_id: User ID for permission filtering
            fuzzy: Enable fuzzy matching
            highlight: Enable result highlighting
            aggregations: Fields to aggregate
        
        Returns:
            SearchResponse with results and metadata
        """
        # Build Elasticsearch query
        es_query = self._build_query(
            query=query,
            filters=filters,
            boost_fields=boost_fields,
            user_id=user_id,
            fuzzy=fuzzy
        )
        
        # Add highlighting
        if highlight:
            es_query["highlight"] = self._build_highlight_config()
        
        # Add aggregations
        if aggregations:
            es_query["aggs"] = self._build_aggregations(aggregations)
        
        # Pagination
        es_query["from"] = (page - 1) * page_size
        es_query["size"] = page_size
        
        # Execute search
        try:
            response = self.es.search(
                index=self.index_name,
                body=es_query,
                request_timeout=30
            )
            
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Elasticsearch search error: {e}")
            raise
    
    def _build_query(
        self,
        query: str,
        filters: Optional[Dict],
        boost_fields: Optional[Dict[str, float]],
        user_id: Optional[int],
        fuzzy: bool
    ) -> Dict:
        """
        Build Elasticsearch query DSL
        
        Query strategy:
        1. Multi-match across title, content, summary
        2. Apply field boosts
        3. Add filters (must clauses)
        4. Add permission filters
        5. Add fuzzy matching if enabled
        6. Boost recent documents
        """
        # Default boost values
        if not boost_fields:
            boost_fields = {
                'title': 2.0,
                'content': 1.0,
                'summary': 1.5,
                'tags': 1.3
            }
        
        # Build multi-match query
        must_clauses = []
        
        # Main search query
        multi_match = {
            "multi_match": {
                "query": query,
                "fields": [
                    f"title^{boost_fields.get('title', 2.0)}",
                    f"content^{boost_fields.get('content', 1.0)}",
                    f"summary^{boost_fields.get('summary', 1.5)}",
                    f"tags^{boost_fields.get('tags', 1.3)}"
                ],
                "type": "best_fields",
                "operator": "or",
                "minimum_should_match": "75%"
            }
        }
        
        if fuzzy:
            multi_match["multi_match"]["fuzziness"] = "AUTO"
            multi_match["multi_match"]["prefix_length"] = 2
        
        must_clauses.append(multi_match)
        
        # Phrase boost (exact phrase gets bonus)
        should_clauses = [
            {
                "match_phrase": {
                    "title": {
                        "query": query,
                        "boost": 3.0
                    }
                }
            },
            {
                "match_phrase": {
                    "content": {
                        "query": query,
                        "boost": 1.5
                    }
                }
            }
        ]
        
        # Build filter clauses
        filter_clauses = []
        
        # Permission filtering
        if user_id:
            filter_clauses.append(
                self._build_permission_filter(user_id)
            )
        
        # Structured filters
        if filters:
            if 'date_after' in filters:
                filter_clauses.append({
                    "range": {
                        "created_at": {
                            "gte": filters['date_after']
                        }
                    }
                })
            
            if 'date_before' in filters:
                filter_clauses.append({
                    "range": {
                        "created_at": {
                            "lte": filters['date_before']
                        }
                    }
                })
            
            if 'type' in filters:
                filter_clauses.append({
                    "term": {
                        "document_type": filters['type']
                    }
                })
            
            if 'tags' in filters:
                filter_clauses.append({
                    "terms": {
                        "tags": filters['tags']
                    }
                })
            
            if 'user' in filters:
                filter_clauses.append({
                    "term": {
                        "owner_id": filters['user']
                    }
                })
            
            if 'domain' in filters:
                filter_clauses.append({
                    "term": {
                        "domain": filters['domain']
                    }
                })
        
        # Active documents only
        filter_clauses.append({
            "term": {
                "status": "active"
            }
        })
        
        # Function score for recency boost
        function_score = {
            "function_score": {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "should": should_clauses,
                        "filter": filter_clauses,
                        "minimum_should_match": 1
                    }
                },
                "functions": [
                    {
                        "gauss": {
                            "created_at": {
                                "origin": "now",
                                "scale": "30d",
                                "decay": 0.5
                            }
                        },
                        "weight": 0.5
                    },
                    {
                        "field_value_factor": {
                            "field": "view_count",
                            "factor": 0.1,
                            "modifier": "log1p",
                            "missing": 0
                        },
                        "weight": 0.3
                    }
                ],
                "score_mode": "sum",
                "boost_mode": "multiply"
            }
        }
        
        return {
            "query": function_score,
            "track_total_hits": True
        }
    
    def _build_permission_filter(self, user_id: int) -> Dict:
        """
        Build permission filter
        
        User can see documents if:
        1. They own the document
        2. Document is public
        3. They have explicit permission
        """
        return {
            "bool": {
                "should": [
                    # Owner
                    {
                        "term": {
                            "owner_id": str(user_id)
                        }
                    },
                    # Public documents
                    {
                        "term": {
                            "metadata.visibility": "public"
                        }
                    },
                    # Explicit permission
                    {
                        "nested": {
                            "path": "permissions",
                            "query": {
                                "bool": {
                                    "must": [
                                        {
                                            "term": {
                                                "permissions.user_id": str(user_id)
                                            }
                                        },
                                        {
                                            "terms": {
                                                "permissions.access_level": ["read", "write", "admin"]
                                            }
                                        }
                                    ]
                                }
                            }
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    
    def _build_highlight_config(self) -> Dict:
        """Configure result highlighting"""
        return {
            "fields": {
                "title": {
                    "number_of_fragments": 0,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                },
                "content": {
                    "fragment_size": 150,
                    "number_of_fragments": 3,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                },
                "summary": {
                    "number_of_fragments": 1,
                    "pre_tags": ["<mark>"],
                    "post_tags": ["</mark>"]
                }
            },
            "require_field_match": False
        }
    
    def _build_aggregations(self, fields: List[str]) -> Dict:
        """Build aggregations for faceted search"""
        aggs = {}
        
        for field in fields:
            if field == "type":
                aggs["document_types"] = {
                    "terms": {
                        "field": "document_type",
                        "size": 20
                    }
                }
            elif field == "tags":
                aggs["tags"] = {
                    "terms": {
                        "field": "tags",
                        "size": 50
                    }
                }
            elif field == "date":
                aggs["date_histogram"] = {
                    "date_histogram": {
                        "field": "created_at",
                        "calendar_interval": "month",
                        "format": "yyyy-MM"
                    }
                }
            elif field == "owner":
                aggs["owners"] = {
                    "terms": {
                        "field": "owner_id",
                        "size": 20
                    }
                }
            elif field == "domain":
                aggs["domains"] = {
                    "terms": {
                        "field": "domain",
                        "size": 10
                    }
                }
        
        return aggs
    
    def _parse_response(self, response: Dict) -> SearchResponse:
        """Parse Elasticsearch response"""
        hits = response['hits']['hits']
        total_hits = response['hits']['total']['value']
        took_ms = response['took']
        max_score = response['hits']['max_score'] or 0.0
        
        results = []
        for hit in hits:
            source = hit['_source']
            highlights = hit.get('highlight', {})
            
            result = SearchResult(
                document_id=int(source['id']),
                title=source['title'],
                summary=source.get('summary', ''),
                score=hit['_score'],
                highlights=highlights,
                metadata={
                    'created_at': source.get('created_at'),
                    'owner_name': source.get('owner_name'),
                    'tags': source.get('tags', []),
                    'view_count': source.get('view_count', 0),
                    'file_extension': source.get('file_extension'),
                },
                document_type=source.get('document_type', 'unknown')
            )
            results.append(result)
        
        # Parse aggregations if present
        aggregations = None
        if 'aggregations' in response:
            aggregations = self._parse_aggregations(response['aggregations'])
        
        return SearchResponse(
            results=results,
            total_hits=total_hits,
            took_ms=took_ms,
            max_score=max_score,
            aggregations=aggregations
        )
    
    def _parse_aggregations(self, aggs: Dict) -> Dict:
        """Parse aggregation results"""
        parsed = {}
        
        for agg_name, agg_data in aggs.items():
            if 'buckets' in agg_data:
                parsed[agg_name] = [
                    {
                        'key': bucket['key'],
                        'count': bucket['doc_count']
                    }
                    for bucket in agg_data['buckets']
                ]
        
        return parsed
    
    def suggest(self, prefix: str, size: int = 10) -> List[str]:
        """
        Autocomplete suggestions
        
        Uses completion suggester on title field
        """
        try:
            response = self.es.search(
                index=self.index_name,
                body={
                    "suggest": {
                        "title-suggest": {
                            "prefix": prefix,
                            "completion": {
                                "field": "title.suggest",
                                "size": size,
                                "skip_duplicates": True
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for option in response['suggest']['title-suggest'][0]['options']:
                suggestions.append(option['text'])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggest error: {e}")
            return []
    
    def more_like_this(
        self,
        document_id: int,
        size: int = 10
    ) -> List[SearchResult]:
        """
        Find similar documents using More Like This query
        
        Uses term frequency analysis to find similar documents
        """
        try:
            response = self.es.search(
                index=self.index_name,
                body={
                    "query": {
                        "more_like_this": {
                            "fields": ["title", "content", "tags"],
                            "like": [
                                {
                                    "_index": self.index_name,
                                    "_id": str(document_id)
                                }
                            ],
                            "min_term_freq": 2,
                            "max_query_terms": 25,
                            "min_doc_freq": 5,
                            "minimum_should_match": "30%"
                        }
                    },
                    "size": size
                }
            )
            
            return self._parse_response(response).results
            
        except Exception as e:
            logger.error(f"More like this error: {e}")
            return []


# Example usage
def example_search():
    """Example search queries"""
    
    es_client = Elasticsearch(['http://localhost:9200'])
    search_engine = ElasticsearchSearchEngine(es_client)
    
    # Simple search
    results = search_engine.search(
        query="personal budget",
        page=1,
        page_size=10
    )
    
    print(f"Found {results.total_hits} documents in {results.took_ms}ms")
    for result in results.results:
        print(f"- {result.title} (score: {result.score:.2f})")
    
    # Filtered search
    results = search_engine.search(
        query="SGB IX assistance",
        filters={
            'date_after': '2024-01-01',
            'type': 'legal_document',
            'tags': ['disability', 'benefits']
        },
        user_id=123
    )
    
    # Autocomplete
    suggestions = search_engine.suggest("pers")
    print(f"Suggestions: {suggestions}")
    # Output: ['personal budget', 'personal assistance', 'persönliches Budget']
    
    # Find similar documents
    similar = search_engine.more_like_this(document_id=456, size=5)
    print(f"Documents similar to 456:")
    for doc in similar:
        print(f"- {doc.title}")
```

---

## 📊 Indexing Pipeline

### Bulk Indexing

```python
# ios_core/search/indexer.py

from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, streaming_bulk
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """
    Handles document indexing to Elasticsearch
    
    Features:
    - Bulk indexing for performance
    - Incremental updates
    - Error handling and retry
    - Progress tracking
    """
    
    def __init__(self, es_client: Elasticsearch, index_name: str):
        self.es = es_client
        self.index_name = index_name
    
    def index_document(self, document: Dict) -> bool:
        """Index single document"""
        try:
            self.es.index(
                index=self.index_name,
                id=document['id'],
                document=self._prepare_document(document),
                refresh='wait_for'  # Make immediately searchable
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index document {document['id']}: {e}")
            return False
    
    def bulk_index(
        self,
        documents: List[Dict],
        chunk_size: int = 500,
        max_retries: int = 3
    ) -> Dict[str, int]:
        """
        Bulk index multiple documents
        
        Returns:
            Dict with success/failure counts
        """
        actions = [
            {
                '_index': self.index_name,
                '_id': doc['id'],
                '_source': self._prepare_document(doc)
            }
            for doc in documents
        ]
        
        success_count = 0
        error_count = 0
        
        try:
            # Use streaming bulk for large datasets
            for ok, response in streaming_bulk(
                self.es,
                actions,
                chunk_size=chunk_size,
                max_retries=max_retries,
                raise_on_error=False
            ):
                if ok:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(f"Indexing error: {response}")
            
            logger.info(
                f"Bulk indexing complete: {success_count} success, "
                f"{error_count} errors"
            )
            
        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
        
        return {
            'success': success_count,
            'errors': error_count,
            'total': len(documents)
        }
    
    def update_document(
        self,
        document_id: int,
        updates: Dict
    ) -> bool:
        """Partial update of document"""
        try:
            self.es.update(
                index=self.index_name,
                id=document_id,
                doc=updates,
                refresh='wait_for'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            return False
    
    def delete_document(self, document_id: int) -> bool:
        """Delete document from index"""
        try:
            self.es.delete(
                index=self.index_name,
                id=document_id,
                refresh='wait_for'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    def reindex_all(
        self,
        batch_size: int = 1000,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, int]:
        """
        Reindex all documents from database
        
        Used for:
        - Initial index creation
        - Schema changes
        - Index recovery
        """
        from ios_core.models import Document
        
        total_docs = Document.objects.filter(status='active').count()
        processed = 0
        stats = {'success': 0, 'errors': 0}
        
        logger.info(f"Starting reindex of {total_docs} documents")
        
        # Process in batches
        for offset in range(0, total_docs, batch_size):
            documents = Document.objects.filter(
                status='active'
            )[offset:offset + batch_size]
            
            # Convert to dict
            doc_dicts = [self._document_to_dict(doc) for doc in documents]
            
            # Bulk index batch
            batch_stats = self.bulk_index(doc_dicts)
            stats['success'] += batch_stats['success']
            stats['errors'] += batch_stats['errors']
            
            processed += len(documents)
            
            if progress_callback:
                progress_callback(processed, total_docs)
            
            logger.info(f"Processed {processed}/{total_docs} documents")
        
        logger.info(
            f"Reindex complete: {stats['success']} indexed, "
            f"{stats['errors']} errors"
        )
        
        return stats
    
    def _prepare_document(self, doc: Dict) -> Dict:
        """Prepare document for indexing"""
        prepared = {
            'id': str(doc['id']),
            'title': doc['title'],
            'content': doc.get('content', ''),
            'summary': doc.get('summary', ''),
            'tags': doc.get('tags', []),
            'document_type': doc.get('document_type', 'general'),
            'created_at': doc.get('created_at'),
            'updated_at': doc.get('updated_at'),
            'owner_id': str(doc.get('owner_id')),
            'owner_name': doc.get('owner_name', ''),
            'language': doc.get('language', 'de'),
            'view_count': doc.get('view_count', 0),
            'download_count': doc.get('download_count', 0),
            'file_size': doc.get('file_size'),
            'file_extension': doc.get('file_extension'),
            'domain': doc.get('domain'),
            'category': doc.get('category'),
            'status': doc.get('status', 'active'),
            'metadata': doc.get('metadata', {}),
            'embedding_id': doc.get('embedding_id')
        }
        
        # Add permissions
        if 'permissions' in doc:
            prepared['permissions'] = doc['permissions']
        
        return prepared
    
    def _document_to_dict(self, document) -> Dict:
        """Convert Django model to dict for indexing"""
        return {
            'id': document.id,
            'title': document.title,
            'content': document.content,
            'summary': document.summary,
            'tags': [tag.name for tag in document.tags.all()],
            'document_type': document.document_type,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
            'owner_id': document.owner_id,
            'owner_name': document.owner.get_full_name(),
            'language': document.language,
            'view_count': document.view_count,
            'download_count': document.download_count,
            'file_size': document.file_size,
            'file_extension': document.file_extension,
            'domain': document.domain.slug if document.domain else None,
            'category': document.category,
            'status': document.status,
            'metadata': document.metadata,
            'embedding_id': document.embedding_id,
            'permissions': [
                {
                    'user_id': perm.user_id,
                    'role': perm.role,
                    'access_level': perm.access_level
                }
                for perm in document.permissions.all()
            ]
        }


# Real-time indexing via signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from ios_core.models import Document

@receiver(post_save, sender=Document)
def index_document_on_save(sender, instance, created, **kwargs):
    """Automatically index document when saved"""
    from ios_core.search import get_indexer
    
    indexer = get_indexer()
    
    if created:
        logger.info(f"Indexing new document: {instance.id}")
    else:
        logger.info(f"Updating document in index: {instance.id}")
    
    # Index asynchronously (Celery task)
    from ios_core.tasks import index_document_task
    index_document_task.delay(instance.id)

@receiver(post_delete, sender=Document)
def remove_document_from_index(sender, instance, **kwargs):
    """Remove document from index when deleted"""
    from ios_core.search import get_indexer
    
    indexer = get_indexer()
    logger.info(f"Removing document from index: {instance.id}")
    
    indexer.delete_document(instance.id)
```

---

## 🔧 Index Management

### Index Creation Script

```bash
#!/bin/bash
# scripts/elasticsearch/create_index.sh
# Create Elasticsearch index with proper mappings

INDEX_NAME="documents"
ES_HOST="http://localhost:9200"

# Create index with mappings
curl -X PUT "$ES_HOST/$INDEX_NAME" \
  -H 'Content-Type: application/json' \
  -d @elasticsearch_mappings.json

# Check index status
curl -X GET "$ES_HOST/$INDEX_NAME/_settings?pretty"
curl -X GET "$ES_HOST/$INDEX_NAME/_mapping?pretty"

# Load synonyms
curl -X PUT "$ES_HOST/$INDEX_NAME/_settings" \
  -H 'Content-Type: application/json' \
  -d '{
    "index": {
      "analysis": {
        "filter": {
          "ios_synonym": {
            "type": "synonym",
            "synonyms": [
              "budget, haushalt, etat",
              "assistance, hilfe, unterstützung",
              "disability, behinderung",
              "personal, persönlich"
            ]
          }
        }
      }
    }
  }'

echo "Index created successfully!"
```

### Reindexing Script

```python
# scripts/elasticsearch/reindex.py

import sys
from django.core.management.base import BaseCommand
from ios_core.search import get_indexer
from tqdm import tqdm

class Command(BaseCommand):
    help = 'Reindex all documents to Elasticsearch'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of documents per batch'
        )
    
    def handle(self, *args, **options):
        indexer = get_indexer()
        batch_size = options['batch_size']
        
        self.stdout.write("Starting reindex...")
        
        # Progress bar callback
        pbar = None
        def progress(current, total):
            nonlocal pbar
            if pbar is None:
                pbar = tqdm(total=total, desc="Indexing")
            pbar.update(current - pbar.n)
        
        stats = indexer.reindex_all(
            batch_size=batch_size,
            progress_callback=progress
        )
        
        if pbar:
            pbar.close()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Reindex complete: {stats['success']} documents indexed, "
                f"{stats['errors']} errors"
            )
        )
```

---

**Продолжение следует...**

Создано:
- ✅ Полная схема Elasticsearch индекса
- ✅ Custom analyzers (German + multilingual)
- ✅ Комплексный поисковый движок
- ✅ Bulk indexing pipeline
- ✅ Real-time indexing via signals
- ✅ Index management scripts

**Следующие разделы:**
1. Vector Search (Qdrant implementation)
2. Hybrid Search Algorithm
3. Search Analytics
4. Performance Tuning

**Готовы продолжить с Vector Search?**