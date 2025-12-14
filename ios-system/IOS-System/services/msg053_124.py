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