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