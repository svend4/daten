"""
Neural Search Engine
Combines semantic and keyword search with intelligent ranking
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import asyncio

from ..ml.embeddings import embedding_service
from ..ml.bert_client import bert_client
from ..elasticsearch_client import es_client
from .query_understanding import query_analyzer
from .hybrid_ranking import hybrid_ranker
from .search_analytics import search_analytics

logger = logging.getLogger(__name__)


class NeuralSearchEngine:
    """
    Advanced neural search combining multiple signals
    
    Features:
    - Semantic search (BERT embeddings)
    - Keyword search (Elasticsearch)
    - Hybrid ranking (ML-based fusion)
    - Query understanding (intent, entities)
    - Personalization (user preferences)
    - Analytics (search quality metrics)
    
    Usage:
        engine = NeuralSearchEngine()
        
        results = await engine.search(
            query="Persönliches Budget beantragen",
            user_id="user123",
            limit=20
        )
    """
    
    def __init__(self):
        self.semantic_weight = 0.6
        self.keyword_weight = 0.4
        self.enable_query_expansion = True
        self.enable_personalization = True
    
    async def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        domain_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        language: str = "de"
    ) -> Dict:
        """
        Execute neural search
        
        Args:
            query: Search query
            user_id: User ID for personalization
            domain_filter: Filter by domain
            limit: Max results
            offset: Pagination offset
            language: Query language (de, ru, en)
        
        Returns:
            Search results with scores and metadata
        """
        
        start_time = datetime.utcnow()
        
        # 1. Analyze query
        query_info = await query_analyzer.analyze(
            query=query,
            language=language
        )
        
        # 2. Expand query if enabled
        expanded_queries = [query]
        if self.enable_query_expansion and query_info.get("expansion"):
            expanded_queries.extend(query_info["expansion"])
        
        # 3. Execute parallel searches
        semantic_results, keyword_results = await asyncio.gather(
            self._semantic_search(
                queries=expanded_queries,
                domain_filter=domain_filter,
                limit=limit * 2  # Get more for ranking
            ),
            self._keyword_search(
                queries=expanded_queries,
                domain_filter=domain_filter,
                limit=limit * 2,
                language=language
            )
        )
        
        # 4. Extract entities for filtering
        entities = query_info.get("entities", [])
        
        # 5. Merge and rank results
        merged_results = await hybrid_ranker.rank(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            query_info=query_info,
            semantic_weight=self.semantic_weight,
            keyword_weight=self.keyword_weight,
            entities=entities
        )
        
        # 6. Apply personalization
        if self.enable_personalization and user_id:
            merged_results = await self._apply_personalization(
                results=merged_results,
                user_id=user_id,
                query_info=query_info
            )
        
        # 7. Pagination
        total = len(merged_results)
        paginated_results = merged_results[offset:offset + limit]
        
        # 8. Log analytics
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        await search_analytics.log_search(
            query=query,
            user_id=user_id,
            results_count=total,
            execution_time=execution_time,
            query_info=query_info
        )
        
        return {
            "query": query,
            "query_info": query_info,
            "results": paginated_results,
            "total": total,
            "limit": limit,
            "offset": offset,
            "execution_time_ms": int(execution_time * 1000),
            "search_strategy": {
                "semantic_weight": self.semantic_weight,
                "keyword_weight": self.keyword_weight,
                "query_expansion": self.enable_query_expansion,
                "personalization": self.enable_personalization and user_id is not None
            }
        }
    
    async def _semantic_search(
        self,
        queries: List[str],
        domain_filter: Optional[str],
        limit: int
    ) -> List[Dict]:
        """Execute semantic search using BERT embeddings"""
        
        try:
            # Search with primary query
            results = await embedding_service.search_similar(
                query=queries[0],
                limit=limit,
                domain_filter=domain_filter,
                score_threshold=0.5
            )
            
            # If query expansion enabled, merge results
            if len(queries) > 1:
                expanded_results = []
                for expanded_query in queries[1:]:
                    expanded = await embedding_service.search_similar(
                        query=expanded_query,
                        limit=limit // 2,
                        domain_filter=domain_filter,
                        score_threshold=0.5
                    )
                    expanded_results.extend(expanded)
                
                # Merge and deduplicate
                seen_ids = {r["id"] for r in results}
                for r in expanded_results:
                    if r["id"] not in seen_ids:
                        results.append(r)
                        seen_ids.add(r["id"])
            
            # Add source marker
            for r in results:
                r["search_type"] = "semantic"
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []
    
    async def _keyword_search(
        self,
        queries: List[str],
        domain_filter: Optional[str],
        limit: int,
        language: str
    ) -> List[Dict]:
        """Execute keyword search using Elasticsearch"""
        
        try:
            # Build Elasticsearch query
            must_clauses = []
            
            # Multi-match on expanded queries
            for query in queries:
                must_clauses.append({
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^3",
                            "content",
                            "metadata.keywords^2"
                        ],
                        "type": "best_fields",
                        "operator": "or",
                        "fuzziness": "AUTO"
                    }
                })
            
            # Domain filter
            filter_clauses = []
            if domain_filter:
                filter_clauses.append({
                    "term": {"domain_name.keyword": domain_filter}
                })
            
            # Build final query
            es_query = {
                "bool": {
                    "should": must_clauses,
                    "filter": filter_clauses,
                    "minimum_should_match": 1
                }
            }
            
            # Execute search
            response = await es_client.search(
                index="ios_documents",
                body={
                    "query": es_query,
                    "size": limit,
                    "highlight": {
                        "fields": {
                            "title": {},
                            "content": {
                                "fragment_size": 150,
                                "number_of_fragments": 3
                            }
                        }
                    }
                }
            )
            
            # Format results
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    "text": hit["_source"].get("content", "")[:1000],
                    "metadata": hit["_source"].get("metadata", {}),
                    "highlights": hit.get("highlight", {}),
                    "search_type": "keyword"
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Keyword search error: {e}")
            return []
    
    async def _apply_personalization(
        self,
        results: List[Dict],
        user_id: str,
        query_info: Dict
    ) -> List[Dict]:
        """Apply personalization to results"""
        
        try:
            # Get user preferences
            user_prefs = await self._get_user_preferences(user_id)
            
            # Boost preferred domains
            preferred_domains = user_prefs.get("preferred_domains", [])
            
            for result in results:
                domain = result.get("metadata", {}).get("domain_name")
                
                if domain in preferred_domains:
                    # Boost score by 20%
                    result["final_score"] = result["final_score"] * 1.2
                    result["personalized"] = True
            
            # Re-sort by final score
            results.sort(key=lambda x: x["final_score"], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Personalization error: {e}")
            return results
    
    async def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user search preferences"""
        
        # This would typically load from database
        # For now, return defaults
        return {
            "preferred_domains": [],
            "recent_queries": [],
            "frequent_terms": []
        }
    
    async def suggest(
        self,
        query: str,
        limit: int = 10,
        language: str = "de"
    ) -> List[str]:
        """
        Get query suggestions (autocomplete)
        
        Args:
            query: Partial query
            limit: Max suggestions
            language: Language
        
        Returns:
            List of suggested queries
        """
        
        try:
            # Use Elasticsearch completion suggester
            response = await es_client.search(
                index="ios_documents",
                body={
                    "suggest": {
                        "query_suggestion": {
                            "prefix": query,
                            "completion": {
                                "field": "suggest",
                                "size": limit,
                                "skip_duplicates": True
                            }
                        }
                    }
                }
            )
            
            suggestions = []
            for option in response["suggest"]["query_suggestion"][0]["options"]:
                suggestions.append(option["text"])
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Suggestion error: {e}")
            return []


# Global neural search engine
neural_search = NeuralSearchEngine()