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