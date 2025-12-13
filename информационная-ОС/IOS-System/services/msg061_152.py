"""
Advanced Language Detection
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import Counter
import re

from langdetect import detect, detect_langs, LangDetectException
from lingua import Language, LanguageDetectorBuilder

logger = logging.getLogger(__name__)


class LanguageDetector:
    """
    Advanced language detection
    
    Features:
    - Multiple detection engines
    - Confidence scoring
    - Mixed-language detection
    - Script-based fallback
    - Domain-specific hints
    
    Usage:
        detector = LanguageDetector()
        
        # Detect language
        result = detector.detect("Das ist ein deutscher Text")
        # {'language': 'de', 'confidence': 0.99}
        
        # Detect multiple languages
        languages = detector.detect_multiple("Hello, wie geht's?")
        # [('en', 0.6), ('de', 0.4)]
    """
    
    # Cyrillic script pattern
    CYRILLIC_PATTERN = re.compile(r'[а-яА-ЯёЁ]')
    
    # German-specific characters
    GERMAN_PATTERN = re.compile(r'[äöüßÄÖÜ]')
    
    # Legal terminology by language
    LEGAL_KEYWORDS = {
        'de': {
            'antrag', 'bescheid', 'widerspruch', 'klage', 'urteil',
            'gesetz', 'paragraph', 'sgb', 'absatz', 'behörde'
        },
        'ru': {
            'заявление', 'решение', 'возражение', 'иск', 'постановление',
            'закон', 'статья', 'пункт', 'орган', 'власть'
        },
        'en': {
            'application', 'decision', 'objection', 'lawsuit', 'judgment',
            'law', 'section', 'article', 'authority', 'government'
        }
    }
    
    def __init__(self):
        # Initialize Lingua detector (more accurate for European languages)
        self.lingua_detector = LanguageDetectorBuilder.from_languages(
            Language.GERMAN,
            Language.RUSSIAN,
            Language.ENGLISH
        ).build()
    
    def detect(
        self,
        text: str,
        hint: Optional[str] = None
    ) -> Dict:
        """
        Detect primary language
        
        Args:
            text: Input text
            hint: Domain hint (e.g., 'legal')
        
        Returns:
            Detection result with confidence
        """
        
        if not text or len(text.strip()) < 3:
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'method': 'insufficient_text'
            }
        
        # Try multiple detection methods
        detections = []
        
        # 1. Script-based detection (fast, reliable for Cyrillic)
        script_result = self._detect_by_script(text)
        if script_result:
            detections.append(script_result)
        
        # 2. Lingua detection (accurate for European languages)
        try:
            lingua_result = self._detect_lingua(text)
            if lingua_result:
                detections.append(lingua_result)
        except Exception as e:
            logger.debug(f"Lingua detection failed: {e}")
        
        # 3. langdetect (good for general text)
        try:
            langdetect_result = self._detect_langdetect(text)
            if langdetect_result:
                detections.append(langdetect_result)
        except Exception as e:
            logger.debug(f"langdetect failed: {e}")
        
        # 4. Keyword-based detection (for domain-specific text)
        if hint == 'legal':
            keyword_result = self._detect_by_keywords(text)
            if keyword_result:
                detections.append(keyword_result)
        
        # Combine results
        if not detections:
            return {
                'language': 'unknown',
                'confidence': 0.0,
                'method': 'all_failed'
            }
        
        # Vote on most common detection
        lang_votes = Counter([d['language'] for d in detections])
        most_common = lang_votes.most_common(1)[0]
        
        # Calculate average confidence for winner
        winner_lang = most_common[0]
        winner_detections = [d for d in detections if d['language'] == winner_lang]
        avg_confidence = sum(d['confidence'] for d in winner_detections) / len(winner_detections)
        
        return {
            'language': winner_lang,
            'confidence': round(avg_confidence, 2),
            'method': 'ensemble',
            'votes': dict(lang_votes),
            'detections': len(detections)
        }
    
    def detect_multiple(
        self,
        text: str,
        min_confidence: float = 0.3
    ) -> List[Tuple[str, float]]:
        """
        Detect multiple languages in mixed text
        
        Args:
            text: Input text
            min_confidence: Minimum confidence threshold
        
        Returns:
            List of (language, confidence) tuples
        """
        
        try:
            # Use langdetect's detect_langs for probabilities
            detections = detect_langs(text)
            
            results = [
                (str(det.lang), det.prob)
                for det in detections
                if det.prob >= min_confidence
            ]
            
            return results
            
        except LangDetectException:
            # Fallback to single detection
            result = self.detect(text)
            if result['confidence'] >= min_confidence:
                return [(result['language'], result['confidence'])]
            return []
    
    def _detect_by_script(self, text: str) -> Optional[Dict]:
        """Detect by script (Cyrillic, German umlauts, etc.)"""
        
        # Check for Cyrillic
        cyrillic_chars = len(self.CYRILLIC_PATTERN.findall(text))
        total_chars = len(re.findall(r'[a-zA-Zа-яА-ЯёЁäöüßÄÖÜ]', text))
        
        if total_chars == 0:
            return None
        
        cyrillic_ratio = cyrillic_chars / total_chars
        
        if cyrillic_ratio > 0.3:
            return {
                'language': 'ru',
                'confidence': min(0.95, 0.7 + cyrillic_ratio * 0.3),
                'method': 'script_cyrillic'
            }
        
        # Check for German umlauts
        german_chars = len(self.GERMAN_PATTERN.findall(text))
        german_ratio = german_chars / total_chars
        
        if german_ratio > 0.02:  # Even 2% is strong signal
            return {
                'language': 'de',
                'confidence': min(0.85, 0.6 + german_ratio * 2),
                'method': 'script_german'
            }
        
        return None
    
    def _detect_lingua(self, text: str) -> Optional[Dict]:
        """Detect using Lingua library"""
        
        confidence_values = self.lingua_detector.compute_language_confidence_values(text)
        
        if not confidence_values:
            return None
        
        # Get top result
        top = confidence_values[0]
        
        # Map Lingua language to ISO code
        lang_map = {
            Language.GERMAN: 'de',
            Language.RUSSIAN: 'ru',
            Language.ENGLISH: 'en'
        }
        
        lang_code = lang_map.get(top.language)
        if not lang_code:
            return None
        
        return {
            'language': lang_code,
            'confidence': round(top.value, 2),
            'method': 'lingua'
        }
    
    def _detect_langdetect(self, text: str) -> Optional[Dict]:
        """Detect using langdetect library"""
        
        try:
            lang = detect(text)
            
            # Get confidence from detect_langs
            detections = detect_langs(text)
            confidence = next(
                (d.prob for d in detections if str(d.lang) == lang),
                0.5
            )
            
            return {
                'language': lang,
                'confidence': round(confidence, 2),
                'method': 'langdetect'
            }
            
        except LangDetectException:
            return None
    
    def _detect_by_keywords(self, text: str) -> Optional[Dict]:
        """Detect by legal keywords"""
        
        text_lower = text.lower()
        
        scores = {}
        for lang, keywords in self.LEGAL_KEYWORDS.items():
            # Count matching keywords
            matches = sum(1 for kw in keywords if kw in text_lower)
            if matches > 0:
                scores[lang] = matches / len(keywords)
        
        if not scores:
            return None
        
        # Get best match
        best_lang = max(scores, key=scores.get)
        confidence = min(0.8, 0.5 + scores[best_lang])
        
        return {
            'language': best_lang,
            'confidence': round(confidence, 2),
            'method': 'keywords'
        }


# Global language detector
language_detector = LanguageDetector()