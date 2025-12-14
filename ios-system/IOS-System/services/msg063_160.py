"""
Query Optimization
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Optimize search queries for performance
    
    Features:
    - Query rewriting
    - Stop word removal
    - Synonym expansion (cached)
    - Query complexity analysis
    - Performance hints
    
    Usage:
        optimizer = QueryOptimizer()
        
        optimized = optimizer.optimize_query(
            query="das persönliche budget für menschen",
            language="de"
        )
    """
    
    # Stop words by language
    STOP_WORDS = {
        'de': {
            'der', 'die', 'das', 'den', 'dem', 'des',
            'ein', 'eine', 'eines', 'einem', 'einen',
            'und', 'oder', 'aber', 'für', 'von', 'zu',
            'in', 'auf', 'mit', 'bei', 'nach', 'über'
        },
        'ru': {
            'и', 'в', 'не', 'на', 'с', 'что', 'к',
            'по', 'для', 'как', 'от', 'за', 'из'
        },
        'en': {
            'the', 'a', 'an', 'and', 'or', 'but',
            'for', 'of', 'to', 'in', 'on', 'with'
        }
    }
    
    def optimize_query(
        self,
        query: str,
        language: str = "de",
        remove_stop_words: bool = True,
        min_word_length: int = 2
    ) -> Dict:
        """
        Optimize search query
        
        Args:
            query: Original query
            language: Query language
            remove_stop_words: Remove stop words
            min_word_length: Minimum word length
        
        Returns:
            Optimization result
        """
        
        original = query
        words = query.lower().split()
        
        # Remove stop words
        if remove_stop_words:
            stop_words = self.STOP_WORDS.get(language, set())
            words = [w for w in words if w not in stop_words]
        
        # Remove short words
        words = [w for w in words if len(w) >= min_word_length]
        
        # Rebuild query
        optimized = " ".join(words)
        
        # Analyze complexity
        complexity = self._analyze_complexity(optimized)
        
        return {
            "original": original,
            "optimized": optimized,
            "removed_words": len(original.split()) - len(words),
            "complexity": complexity,
            "recommendations": self._get_recommendations(complexity)
        }
    
    def _analyze_complexity(self, query: str) -> str:
        """Analyze query complexity"""
        
        word_count = len(query.split())
        
        if word_count <= 2:
            return "simple"
        elif word_count <= 5:
            return "medium"
        else:
            return "complex"
    
    def _get_recommendations(self, complexity: str) -> List[str]:
        """Get optimization recommendations"""
        
        recommendations = []
        
        if complexity == "complex":
            recommendations.append("Consider breaking into multiple queries")
            recommendations.append("Use more specific terms")
        elif complexity == "simple":
            recommendations.append("Could add more context for better results")
        
        return recommendations


# Global query optimizer
query_optimizer = QueryOptimizer()