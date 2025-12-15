"""
Enhanced search with Elasticsearch
"""

from elasticsearch import AsyncElasticsearch
from typing import List, Dict

class ElasticsearchService:
    """Elasticsearch-based search"""
    
    def __init__(self):
        self.es = AsyncElasticsearch(['http://elasticsearch:9200'])
    
    async def index_document(self, doc_id: str, content: Dict):
        """Index document in Elasticsearch"""
        
        await self.es.index(
            index="documents",
            id=doc_id,
            body={
                "title": content["title"],
                "content": content["content"],
                "document_type": content["type"],
                "entities": content["entities"],
                "created_at": content["created_at"],
                "domain": content["domain"],
                # Vector embedding for neural search
                "embedding": content.get("embedding")
            }
        )
    
    async def search(
        self,
        query: str,
        filters: Dict = None,
        size: int = 10,
        search_type: str = "bm25"
    ) -> List[Dict]:
        """Multi-strategy search"""
        
        if search_type == "neural":
            # Neural search with kNN
            query_embedding = await self._get_embedding(query)
            
            body = {
                "knn": {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": size,
                    "num_candidates": 100
                },
                "query": {
                    "bool": {
                        "filter": self._build_filters(filters)
                    }
                }
            }
        else:
            # Traditional BM25
            body = {
                "query": {
                    "bool": {
                        "must": {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^3", "content"],
                                "type": "best_fields"
                            }
                        },
                        "filter": self._build_filters(filters)
                    }
                },
                "size": size
            }
        
        response = await self.es.search(
            index="documents",
            body=body
        )
        
        return self._format_results(response)
    
    async def aggregate(self, field: str, filters: Dict = None):
        """Aggregation for faceted search"""
        
        body = {
            "size": 0,
            "query": {
                "bool": {
                    "filter": self._build_filters(filters)
                }
            },
            "aggs": {
                "by_field": {
                    "terms": {
                        "field": field,
                        "size": 100
                    }
                }
            }
        }
        
        response = await self.es.search(index="documents", body=body)
        return response["aggregations"]["by_field"]["buckets"]