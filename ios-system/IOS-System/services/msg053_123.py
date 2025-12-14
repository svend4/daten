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