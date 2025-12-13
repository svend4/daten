Отлично! Продолжаем с Day 121-122: Neural Search & Multi-language Support.

Сейчас создам:
1. Neural Search engine combining multiple signals
2. Multi-language support (German, Russian, English)
3. Advanced ranking algorithms
4. Query expansion and understanding
5. Cross-lingual search
6. Search analytics and optimization

Файлы:
- Neural search engine
- Multi-language support
- Query understanding
- Hybrid ranking
- Search analytics
- Cross-lingual embeddings
- API routes
- Tests
- Documentation# 🔍 DAY 121-122: NEURAL SEARCH & MULTI-LANGUAGE

---

## 📊 ЦЕЛЬ

Создание продвинутой системы поиска:
- **Neural Search** - комбинация семантического и ключевого поиска
- **Multi-language** - поддержка немецкого, русского, английского
- **Query Understanding** - анализ и расширение запросов
- **Hybrid Ranking** - интеллектуальное ранжирование
- **Cross-lingual Search** - поиск на разных языках
- **Search Analytics** - аналитика и оптимизация

---

## ФАЙЛ 95: `ios_core/search/__init__.py`

```python
"""
Advanced Search Module
"""

from .neural_search import NeuralSearchEngine
from .multi_language import MultiLanguageSupport
from .query_understanding import QueryAnalyzer
from .hybrid_ranking import HybridRanker
from .search_analytics import SearchAnalytics

__all__ = [
    'NeuralSearchEngine',
    'MultiLanguageSupport',
    'QueryAnalyzer',
    'HybridRanker',
    'SearchAnalytics',
]
```

---

## ФАЙЛ 96: `ios_core/search/neural_search.py`

```python
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
```

---

## ФАЙЛ 97: `ios_core/search/multi_language.py`

```python
"""
Multi-language Support
Handles German, Russian, and English
"""

import logging
from typing import Dict, List, Optional
from enum import Enum

from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages"""
    GERMAN = "de"
    RUSSIAN = "ru"
    ENGLISH = "en"


class MultiLanguageSupport:
    """
    Multi-language search support
    
    Features:
    - Automatic language detection
    - Query translation
    - Cross-lingual search
    - Language-specific processing
    
    Usage:
        ml = MultiLanguageSupport()
        
        # Detect language
        lang = ml.detect_language("Persönliches Budget")
        
        # Translate query
        translated = await ml.translate_query(
            query="Personal budget",
            source_lang="en",
            target_lang="de"
        )
    """
    
    # Language-specific stopwords
    STOPWORDS = {
        Language.GERMAN: {
            "der", "die", "das", "und", "oder", "aber", "ein", "eine",
            "von", "zu", "auf", "für", "mit", "bei", "nach", "über",
            "gegen", "durch", "um", "an", "in", "im", "am", "dem", "den"
        },
        Language.RUSSIAN: {
            "и", "в", "не", "на", "с", "что", "к", "по", "для", "как",
            "от", "за", "из", "о", "об", "это", "а", "но", "или"
        },
        Language.ENGLISH: {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "are", "was"
        }
    }
    
    # Common legal terms across languages
    LEGAL_TERMS = {
        Language.GERMAN: {
            "antrag": ["application", "заявление"],
            "bescheid": ["decision", "решение"],
            "widerspruch": ["objection", "возражение"],
            "klage": ["lawsuit", "иск"],
            "urteil": ["judgment", "решение суда"],
            "budget": ["budget", "бюджет"],
            "leistung": ["benefit", "услуга"],
            "hilfe": ["assistance", "помощь"]
        }
    }
    
    def detect_language(self, text: str) -> Language:
        """
        Detect text language
        
        Args:
            text: Input text
        
        Returns:
            Detected language
        """
        
        try:
            lang_code = detect(text)
            
            if lang_code == "de":
                return Language.GERMAN
            elif lang_code == "ru":
                return Language.RUSSIAN
            elif lang_code == "en":
                return Language.ENGLISH
            else:
                # Default to German for legal domain
                return Language.GERMAN
                
        except LangDetectException:
            logger.warning(f"Could not detect language for: {text[:50]}")
            return Language.GERMAN
    
    async def translate_query(
        self,
        query: str,
        source_lang: Optional[Language] = None,
        target_lang: Language = Language.GERMAN
    ) -> str:
        """
        Translate query to target language
        
        Args:
            query: Query text
            source_lang: Source language (auto-detect if None)
            target_lang: Target language
        
        Returns:
            Translated query
        """
        
        # Auto-detect source language
        if source_lang is None:
            source_lang = self.detect_language(query)
        
        # No translation needed
        if source_lang == target_lang:
            return query
        
        try:
            translator = GoogleTranslator(
                source=source_lang.value,
                target=target_lang.value
            )
            
            translated = translator.translate(query)
            logger.info(f"Translated '{query}' from {source_lang} to {target_lang}: '{translated}'")
            
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return query
    
    async def cross_lingual_search(
        self,
        query: str,
        search_languages: List[Language] = None
    ) -> Dict[Language, str]:
        """
        Generate queries for cross-lingual search
        
        Args:
            query: Original query
            search_languages: Languages to search (default: all)
        
        Returns:
            Dict mapping language to translated query
        """
        
        if search_languages is None:
            search_languages = [Language.GERMAN, Language.RUSSIAN, Language.ENGLISH]
        
        # Detect source language
        source_lang = self.detect_language(query)
        
        # Translate to each target language
        queries = {source_lang: query}
        
        for target_lang in search_languages:
            if target_lang != source_lang:
                translated = await self.translate_query(
                    query=query,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
                queries[target_lang] = translated
        
        return queries
    
    def remove_stopwords(
        self,
        text: str,
        language: Language
    ) -> str:
        """
        Remove stopwords from text
        
        Args:
            text: Input text
            language: Text language
        
        Returns:
            Text without stopwords
        """
        
        stopwords = self.STOPWORDS.get(language, set())
        
        words = text.lower().split()
        filtered = [w for w in words if w not in stopwords]
        
        return " ".join(filtered)
    
    def expand_legal_terms(
        self,
        query: str,
        language: Language
    ) -> List[str]:
        """
        Expand legal terms with translations
        
        Args:
            query: Query text
            language: Query language
        
        Returns:
            List of expanded queries
        """
        
        expanded = [query]
        
        if language not in self.LEGAL_TERMS:
            return expanded
        
        terms = self.LEGAL_TERMS[language]
        query_lower = query.lower()
        
        for term, translations in terms.items():
            if term in query_lower:
                # Add queries with translations
                for translation in translations:
                    expanded_query = query_lower.replace(term, translation)
                    expanded.append(expanded_query)
        
        return expanded
    
    def get_language_specific_config(
        self,
        language: Language
    ) -> Dict:
        """
        Get language-specific search configuration
        
        Args:
            language: Language
        
        Returns:
            Configuration dict
        """
        
        configs = {
            Language.GERMAN: {
                "analyzer": "german",
                "stemmer": "german",
                "min_word_length": 3,
                "fuzzy_distance": 2
            },
            Language.RUSSIAN: {
                "analyzer": "russian",
                "stemmer": "russian",
                "min_word_length": 3,
                "fuzzy_distance": 1
            },
            Language.ENGLISH: {
                "analyzer": "english",
                "stemmer": "english",
                "min_word_length": 3,
                "fuzzy_distance": 2
            }
        }
        
        return configs.get(language, configs[Language.GERMAN])


# Global multi-language support
multi_language = MultiLanguageSupport()
```

---

## ФАЙЛ 98: `ios_core/search/query_understanding.py`

```python
"""
Query Understanding & Analysis
"""

import logging
from typing import Dict, List, Optional
import re

from ..ml.bert_client import bert_client
from .multi_language import multi_language, Language

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyze and understand search queries
    
    Features:
    - Intent classification
    - Entity extraction
    - Query expansion
    - Spelling correction
    - Language detection
    
    Usage:
        analyzer = QueryAnalyzer()
        
        info = await analyzer.analyze(
            query="Persönliches Budget beantragen",
            language="de"
        )
    """
    
    # Query intent patterns
    INTENT_PATTERNS = {
        "application": [
            r"\b(beantragen|antrag|anmelden|stellen)\b",
            r"\b(apply|application|request)\b",
            r"\b(подать|заявление|заявка)\b"
        ],
        "objection": [
            r"\b(widerspruch|widersprechen|einspruch)\b",
            r"\b(object|objection|appeal)\b",
            r"\b(возражение|возразить|обжалование)\b"
        ],
        "information": [
            r"\b(was ist|wie|wann|wo|warum)\b",
            r"\b(what|how|when|where|why)\b",
            r"\b(что|как|когда|где|почему)\b"
        ],
        "legal_reference": [
            r"§\s*\d+",
            r"\b(SGB|BGB|StGB)\b",
            r"\b(artikel|article|статья)\s*\d+"
        ]
    }
    
    # Common query expansions
    EXPANSIONS = {
        "de": {
            "persönliches budget": ["individuelles budget", "budget für behinderte", "§ 29 SGB IX"],
            "widerspruch": ["einspruch", "widerspruchsverfahren", "rechtsbehelf"],
            "antrag": ["antragsverfahren", "beantragung", "anmeldung"],
            "bescheid": ["verwaltungsakt", "entscheidung", "ablehnungsbescheid"]
        },
        "ru": {
            "личный бюджет": ["индивидуальный бюджет", "бюджет для инвалидов"],
            "возражение": ["апелляция", "обжалование"],
            "заявление": ["заявка", "запрос"]
        },
        "en": {
            "personal budget": ["individual budget", "disability budget"],
            "objection": ["appeal", "complaint"],
            "application": ["request", "claim"]
        }
    }
    
    async def analyze(
        self,
        query: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Analyze query and extract information
        
        Args:
            query: Search query
            language: Query language (auto-detect if None)
        
        Returns:
            Query information dict
        """
        
        # Detect language if not provided
        if language is None:
            detected_lang = multi_language.detect_language(query)
            language = detected_lang.value
        
        # Extract entities
        entities = await self._extract_entities(query)
        
        # Classify intent
        intent = self._classify_intent(query)
        
        # Expand query
        expansion = self._expand_query(query, language)
        
        # Extract legal references
        legal_refs = self._extract_legal_references(query)
        
        # Detect question type
        is_question = self._is_question(query)
        
        return {
            "original_query": query,
            "language": language,
            "entities": entities,
            "intent": intent,
            "expansion": expansion,
            "legal_references": legal_refs,
            "is_question": is_question,
            "query_length": len(query.split()),
            "has_special_chars": bool(re.search(r'[§\d]', query))
        }
    
    async def _extract_entities(self, query: str) -> List[Dict]:
        """Extract named entities from query"""
        
        try:
            entities = await bert_client.extract_entities(
                text=query,
                threshold=0.7
            )
            return entities
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return []
    
    def _classify_intent(self, query: str) -> Optional[str]:
        """Classify query intent"""
        
        query_lower = query.lower()
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent
        
        return "general"
    
    def _expand_query(
        self,
        query: str,
        language: str
    ) -> List[str]:
        """Expand query with synonyms and related terms"""
        
        expansions = []
        query_lower = query.lower()
        
        # Get language-specific expansions
        lang_expansions = self.EXPANSIONS.get(language, {})
        
        for term, synonyms in lang_expansions.items():
            if term in query_lower:
                for synonym in synonyms:
                    expanded = query_lower.replace(term, synonym)
                    if expanded != query_lower:
                        expansions.append(expanded)
        
        return expansions[:3]  # Limit to top 3 expansions
    
    def _extract_legal_references(self, query: str) -> List[str]:
        """Extract legal references (§, articles, laws)"""
        
        refs = []
        
        # Paragraph references
        paragraph_pattern = r'§\s*(\d+[a-z]?(?:\s+Abs\.?\s*\d+)?)'
        paragraphs = re.findall(paragraph_pattern, query, re.IGNORECASE)
        refs.extend([f"§ {p}" for p in paragraphs])
        
        # Law codes
        law_pattern = r'\b(SGB|BGB|StGB|VwGO|SGG)\s*-?\s*([IXV]+)\b'
        laws = re.findall(law_pattern, query, re.IGNORECASE)
        refs.extend([f"{law} {num}" for law, num in laws])
        
        return refs
    
    def _is_question(self, query: str) -> bool:
        """Detect if query is a question"""
        
        # Check for question mark
        if '?' in query:
            return True
        
        # Check for question words
        question_words = [
            # German
            r'\b(was|wie|wann|wo|warum|wer|welche|welcher|welches)\b',
            # English
            r'\b(what|how|when|where|why|who|which)\b',
            # Russian
            r'\b(что|как|когда|где|почему|кто|какой|какая|какое)\b'
        ]
        
        for pattern in question_words:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False


# Global query analyzer
query_analyzer = QueryAnalyzer()
```

---

## ФАЙЛ 99: `ios_core/search/hybrid_ranking.py`

```python
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
```

---

**Продолжаем?** Осталось создать:
- Search Analytics
- API Routes
- Tests
- Configuration
- Documentation