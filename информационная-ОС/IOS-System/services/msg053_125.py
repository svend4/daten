"""
Hybrid Ranking System
Combines multiple signals for optimal ranking
"""

import logging
from typing import List, Dict, Optional
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class HybridRanker:
    """
    Hybrid search result ranking
    
    Combines:
    - Semantic similarity scores
    - Keyword match scores
    - Entity relevance
    - Freshness
    - Document quality
    - User signals
    
    Usage:
        ranker = HybridRanker()
        
        ranked = await ranker.rank(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            query_info=query_info
        )
    """
    
    # Feature weights
    WEIGHTS = {
        "semantic_score": 0.35,
        "keyword_score": 0.25,
        "entity_match": 0.15,
        "freshness": 0.10,
        "quality": 0.10,
        "user_signals": 0.05
    }
    
    async def rank(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        query_info: Dict,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4,
        entities: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Rank and merge search results
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            query_info: Query analysis information
            semantic_weight: Weight for semantic scores
            keyword_weight: Weight for keyword scores
            entities: Extracted entities for matching
        
        Returns:
            Ranked and merged results
        """
        
        # 1. Normalize scores
        semantic_results = self._normalize_scores(semantic_results)
        keyword_results = self._normalize_scores(keyword_results)
        
        # 2. Merge results by document ID
        merged = self._merge_results(
            semantic_results,
            keyword_results,
            semantic_weight,
            keyword_weight
        )
        
        # 3. Compute additional signals
        for result in merged:
            # Entity relevance
            result["entity_score"] = self._compute_entity_relevance(
                result,
                entities or []
            )
            
            # Freshness score
            result["freshness_score"] = self._compute_freshness(result)
            
            # Quality score
            result["quality_score"] = self._compute_quality(result)
            
            # User signals (placeholder)
            result["user_score"] = 0.5
        
        # 4. Compute final scores
        for result in merged:
            result["final_score"] = self._compute_final_score(result)
        
        # 5. Sort by final score
        merged.sort(key=lambda x: x["final_score"], reverse=True)
        
        return merged
    
    def _normalize_scores(self, results: List[Dict]) -> List[Dict]:
        """Normalize scores to [0, 1] range"""
        
        if not results:
            return results
        
        scores = [r["score"] for r in results]
        max_score = max(scores)
        min_score = min(scores)
        
        if max_score == min_score:
            for r in results:
                r["normalized_score"] = 1.0
        else:
            for r in results:
                r["normalized_score"] = (
                    (r["score"] - min_score) / (max_score - min_score)
                )
        
        return results
    
    def _merge_results(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict]:
        """Merge results from different sources"""
        
        # Build document map
        doc_map = {}
        
        # Add semantic results
        for result in semantic_results:
            doc_id = result["id"]
            doc_map[doc_id] = {
                **result,
                "semantic_score": result["normalized_score"],
                "keyword_score": 0.0,
                "found_in_semantic": True,
                "found_in_keyword": False
            }
        
        # Add/merge keyword results
        for result in keyword_results:
            doc_id = result["id"]
            
            if doc_id in doc_map:
                # Update existing
                doc_map[doc_id]["keyword_score"] = result["normalized_score"]
                doc_map[doc_id]["found_in_keyword"] = True
                
                # Merge highlights if available
                if "highlights" in result:
                    doc_map[doc_id]["highlights"] = result["highlights"]
            else:
                # Add new
                doc_map[doc_id] = {
                    **result,
                    "semantic_score": 0.0,
                    "keyword_score": result["normalized_score"],
                    "found_in_semantic": False,
                    "found_in_keyword": True
                }
        
        # Compute combined scores
        for doc in doc_map.values():
            doc["combined_score"] = (
                doc["semantic_score"] * semantic_weight +
                doc["keyword_score"] * keyword_weight
            )
        
        return list(doc_map.values())
    
    def _compute_entity_relevance(
        self,
        result: Dict,
        entities: List[Dict]
    ) -> float:
        """Compute entity match score"""
        
        if not entities:
            return 0.5  # Neutral score
        
        text = result.get("text", "").lower()
        matches = 0
        
        for entity in entities:
            entity_text = entity.get("text", "").lower()
            if entity_text in text:
                matches += 1
        
        # Normalize to [0, 1]
        return min(matches / max(len(entities), 1), 1.0)
    
    def _compute_freshness(self, result: Dict) -> float:
        """Compute freshness score based on document age"""
        
        from datetime import datetime, timedelta
        
        # Get document timestamp
        updated_at_str = result.get("metadata", {}).get("updated_at")
        
        if not updated_at_str:
            return 0.5  # Neutral score
        
        try:
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            now = datetime.utcnow()
            age_days = (now - updated_at).days
            
            # Decay function: fresh documents get higher scores
            # Score = 1.0 for documents < 30 days
            # Score = 0.5 for documents ~ 180 days
            # Score = 0.0 for documents > 365 days
            
            if age_days < 30:
                return 1.0
            elif age_days < 180:
                return 1.0 - (age_days - 30) / 300
            else:
                return max(0.0, 1.0 - age_days / 365)
                
        except Exception as e:
            logger.error(f"Freshness calculation error: {e}")
            return 0.5
    
    def _compute_quality(self, result: Dict) -> float:
        """Compute document quality score"""
        
        quality = 0.5  # Base score
        
        # Text length (prefer substantial documents)
        text = result.get("text", "")
        if len(text) > 500:
            quality += 0.2
        
        # Has metadata
        metadata = result.get("metadata", {})
        if metadata:
            quality += 0.1
        
        # Has highlights (indicates good keyword match)
        if result.get("highlights"):
            quality += 0.2
        
        return min(quality, 1.0)
    
    def _compute_final_score(self, result: Dict) -> float:
        """Compute final ranking score"""
        
        score = 0.0
        
        score += result["combined_score"] * (
            self.WEIGHTS["semantic_score"] + self.WEIGHTS["keyword_score"]
        )
        score += result["entity_score"] * self.WEIGHTS["entity_match"]
        score += result["freshness_score"] * self.WEIGHTS["freshness"]
        score += result["quality_score"] * self.WEIGHTS["quality"]
        score += result.get("user_score", 0.5) * self.WEIGHTS["user_signals"]
        
        return score


# Global hybrid ranker
hybrid_ranker = HybridRanker()