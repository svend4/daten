Отлично! Day 125-126 будет посвящен Multi-language Support & Finalization всей AI/ML инфраструктуры.

План Day 125-126:
1. Multi-language document processing
2. Cross-lingual search optimization
3. Language-specific models integration
4. Translation pipelines
5. Multilingual UI support
6. Testing & validation
7. Performance optimization
8. Documentation finalization
9. Deployment guide
10. Week summary

Создадим файлы:
- Multi-language processor
- Language detection service
- Translation service
- Cross-lingual embeddings
- Multilingual search
- Language-specific analyzers
- UI localization
- Tests
- Setup scripts
- Documentation# 🌍 DAY 125-126: MULTI-LANGUAGE SUPPORT & FINALIZATION

---

## 📊 ЦЕЛЬ

Завершение AI/ML инфраструктуры с полноценной поддержкой языков:
- **Multi-language Processing** - обработка немецкого, русского, английского
- **Cross-lingual Search** - поиск на разных языках
- **Translation Pipeline** - автоматический перевод
- **Language Detection** - определение языка
- **Multilingual UI** - интернационализация интерфейса
- **Performance Optimization** - оптимизация производительности

---

## ФАЙЛ 126: `ios_core/i18n/__init__.py`

```python
"""
Internationalization (i18n) Module
"""

from .language_detector import LanguageDetector, language_detector
from .translator import Translator, translator
from .multilingual_processor import MultilingualProcessor, multilingual_processor
from .locale_manager import LocaleManager, locale_manager

__all__ = [
    'LanguageDetector',
    'language_detector',
    'Translator',
    'translator',
    'MultilingualProcessor',
    'multilingual_processor',
    'LocaleManager',
    'locale_manager',
]
```

---

## ФАЙЛ 127: `ios_core/i18n/language_detector.py`

```python
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
```

---

## ФАЙЛ 128: `ios_core/i18n/translator.py`

```python
"""
Translation Service
"""

import logging
from typing import Dict, List, Optional
from functools import lru_cache
import hashlib

from deep_translator import GoogleTranslator, MyMemoryTranslator
import asyncio

logger = logging.getLogger(__name__)


class Translator:
    """
    Multi-engine translation service
    
    Features:
    - Multiple translation engines
    - Caching for efficiency
    - Batch translation
    - Quality assessment
    - Fallback mechanisms
    
    Usage:
        translator = Translator()
        
        # Translate text
        result = await translator.translate(
            text="Personal budget",
            source_lang="en",
            target_lang="de"
        )
        # "Persönliches Budget"
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_size = 1000
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        engine: str = "google"
    ) -> str:
        """
        Translate text
        
        Args:
            text: Source text
            source_lang: Source language (de, ru, en)
            target_lang: Target language
            engine: Translation engine (google, mymemory)
        
        Returns:
            Translated text
        """
        
        # Skip if same language
        if source_lang == target_lang:
            return text
        
        # Check cache
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        if cache_key in self.cache:
            logger.debug(f"Cache hit for: {text[:50]}")
            return self.cache[cache_key]
        
        # Translate
        try:
            if engine == "google":
                translator = GoogleTranslator(
                    source=source_lang,
                    target=target_lang
                )
            elif engine == "mymemory":
                translator = MyMemoryTranslator(
                    source=source_lang,
                    target=target_lang
                )
            else:
                raise ValueError(f"Unknown engine: {engine}")
            
            # Run in thread pool (deep_translator is sync)
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(
                None,
                translator.translate,
                text
            )
            
            # Cache result
            self._cache_translation(cache_key, translated)
            
            logger.info(
                f"Translated '{text[:50]}' from {source_lang} to {target_lang}"
            )
            
            return translated
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            
            # Fallback to secondary engine
            if engine == "google":
                return await self.translate(
                    text, source_lang, target_lang, engine="mymemory"
                )
            
            # Return original if all fail
            return text
    
    async def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """
        Translate multiple texts
        
        Args:
            texts: List of texts
            source_lang: Source language
            target_lang: Target language
        
        Returns:
            List of translations
        """
        
        tasks = [
            self.translate(text, source_lang, target_lang)
            for text in texts
        ]
        
        return await asyncio.gather(*tasks)
    
    async def translate_document(
        self,
        document: Dict,
        target_lang: str,
        fields: List[str] = ["title", "content"]
    ) -> Dict:
        """
        Translate document fields
        
        Args:
            document: Document dict
            target_lang: Target language
            fields: Fields to translate
        
        Returns:
            Translated document
        """
        
        from .language_detector import language_detector
        
        translated = document.copy()
        
        for field in fields:
            if field not in document:
                continue
            
            text = document[field]
            
            # Detect source language
            detection = language_detector.detect(text)
            source_lang = detection['language']
            
            # Translate
            if source_lang != target_lang:
                translated[field] = await self.translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
        
        return translated
    
    def _get_cache_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Generate cache key"""
        
        content = f"{source_lang}:{target_lang}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cache_translation(self, key: str, translation: str):
        """Cache translation with size limit"""
        
        if len(self.cache) >= self.cache_size:
            # Remove oldest (simple FIFO)
            oldest = next(iter(self.cache))
            del self.cache[oldest]
        
        self.cache[key] = translation
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache.clear()
        logger.info("Translation cache cleared")


# Global translator
translator = Translator()
```

---

## ФАЙЛ 129: `ios_core/i18n/multilingual_processor.py`

```python
"""
Multilingual Document Processor
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .language_detector import language_detector
from .translator import translator
from ..ml.embeddings import embedding_service
from ..database import async_session
from ..models import DocumentModel

logger = logging.getLogger(__name__)


class MultilingualProcessor:
    """
    Process documents in multiple languages
    
    Features:
    - Language detection
    - Auto-translation
    - Multi-language indexing
    - Cross-lingual search support
    
    Usage:
        processor = MultilingualProcessor()
        
        # Process document
        result = await processor.process_document(
            doc_id="doc123",
            generate_translations=True
        )
    """
    
    SUPPORTED_LANGUAGES = ['de', 'ru', 'en']
    
    async def process_document(
        self,
        doc_id: str,
        generate_translations: bool = False,
        target_languages: Optional[List[str]] = None
    ) -> Dict:
        """
        Process document for multilingual support
        
        Args:
            doc_id: Document ID
            generate_translations: Auto-translate to other languages
            target_languages: Languages to translate to
        
        Returns:
            Processing result
        """
        
        async with async_session() as session:
            # Get document
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                raise ValueError(f"Document not found: {doc_id}")
            
            # Detect language
            text = f"{doc.title}\n\n{doc.content}"
            detection = language_detector.detect(text, hint='legal')
            
            # Update document metadata
            if not doc.metadata:
                doc.metadata = {}
            
            doc.metadata['detected_language'] = detection['language']
            doc.metadata['language_confidence'] = detection['confidence']
            
            # Generate translations if requested
            translations = {}
            if generate_translations:
                if target_languages is None:
                    target_languages = [
                        lang for lang in self.SUPPORTED_LANGUAGES
                        if lang != detection['language']
                    ]
                
                for target_lang in target_languages:
                    logger.info(
                        f"Translating {doc_id} to {target_lang}"
                    )
                    
                    translated = await translator.translate_document(
                        document={
                            'title': doc.title,
                            'content': doc.content
                        },
                        target_lang=target_lang,
                        fields=['title', 'content']
                    )
                    
                    translations[target_lang] = translated
                
                # Store translations
                doc.metadata['translations'] = translations
            
            # Update multilingual processing timestamp
            doc.metadata['multilingual_processed_at'] = datetime.utcnow().isoformat()
            
            await session.commit()
            
            return {
                'document_id': doc_id,
                'detected_language': detection['language'],
                'confidence': detection['confidence'],
                'translations_generated': list(translations.keys()),
                'translation_count': len(translations)
            }
    
    async def create_multilingual_index(
        self,
        doc_id: str
    ) -> Dict:
        """
        Create embeddings in multiple languages
        
        Args:
            doc_id: Document ID
        
        Returns:
            Indexing result
        """
        
        async with async_session() as session:
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == doc_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                raise ValueError(f"Document not found: {doc_id}")
            
            # Index original
            original_text = f"{doc.title}\n\n{doc.content}"
            
            await embedding_service.index_document(
                doc_id=doc_id,
                text=original_text,
                metadata={
                    **doc.metadata,
                    'language': doc.metadata.get('detected_language', 'de')
                }
            )
            
            indexed_languages = [doc.metadata.get('detected_language', 'de')]
            
            # Index translations if available
            translations = doc.metadata.get('translations', {})
            
            for lang, translation in translations.items():
                translated_text = f"{translation['title']}\n\n{translation['content']}"
                
                # Create separate index entry
                translated_doc_id = f"{doc_id}_{lang}"
                
                await embedding_service.index_document(
                    doc_id=translated_doc_id,
                    text=translated_text,
                    metadata={
                        **doc.metadata,
                        'language': lang,
                        'is_translation': True,
                        'original_doc_id': doc_id
                    }
                )
                
                indexed_languages.append(lang)
            
            return {
                'document_id': doc_id,
                'indexed_languages': indexed_languages,
                'total_indexes': len(indexed_languages)
            }
    
    async def search_multilingual(
        self,
        query: str,
        query_language: Optional[str] = None,
        search_languages: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict:
        """
        Search across multiple languages
        
        Args:
            query: Search query
            query_language: Query language (auto-detect if None)
            search_languages: Languages to search in
            limit: Max results per language
        
        Returns:
            Multilingual search results
        """
        
        # Detect query language if not specified
        if query_language is None:
            detection = language_detector.detect(query, hint='legal')
            query_language = detection['language']
        
        # Default to all languages if not specified
        if search_languages is None:
            search_languages = self.SUPPORTED_LANGUAGES
        
        # Search in each language
        all_results = {}
        
        for target_lang in search_languages:
            # Translate query if needed
            if target_lang != query_language:
                translated_query = await translator.translate(
                    text=query,
                    source_lang=query_language,
                    target_lang=target_lang
                )
            else:
                translated_query = query
            
            # Search
            results = await embedding_service.search_similar(
                query=translated_query,
                limit=limit,
                score_threshold=0.6
            )
            
            # Filter by language
            lang_results = [
                r for r in results
                if r.get('metadata', {}).get('language') == target_lang
            ]
            
            all_results[target_lang] = {
                'query': translated_query,
                'results': lang_results,
                'count': len(lang_results)
            }
        
        return {
            'original_query': query,
            'query_language': query_language,
            'results_by_language': all_results,
            'total_results': sum(
                r['count'] for r in all_results.values()
            )
        }


# Global multilingual processor
multilingual_processor = MultilingualProcessor()
```

---

## ФАЙЛ 130: `ios_core/i18n/locale_manager.py`

```python
"""
Locale Manager
UI localization support
"""

import logging
from typing import Dict, Optional
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class LocaleManager:
    """
    Manage UI translations and localization
    
    Features:
    - Load translation files
    - Get localized strings
    - Fallback to default language
    - Pluralization support
    
    Usage:
        locale = LocaleManager()
        
        # Get translation
        text = locale.get("welcome_message", lang="de")
        # "Willkommen im IOS System"
    """
    
    def __init__(self, locales_dir: str = "locales"):
        self.locales_dir = Path(locales_dir)
        self.translations = {}
        self.default_language = "de"
        
        # Load translations
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files"""
        
        if not self.locales_dir.exists():
            logger.warning(f"Locales directory not found: {self.locales_dir}")
            return
        
        for lang_file in self.locales_dir.glob("*.json"):
            lang_code = lang_file.stem
            
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                
                logger.info(f"Loaded translations for: {lang_code}")
                
            except Exception as e:
                logger.error(f"Failed to load {lang_file}: {e}")
    
    def get(
        self,
        key: str,
        lang: str = "de",
        default: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Get translated string
        
        Args:
            key: Translation key
            lang: Language code
            default: Default value if not found
            **kwargs: Variables for string formatting
        
        Returns:
            Translated string
        """
        
        # Get translation
        if lang in self.translations and key in self.translations[lang]:
            text = self.translations[lang][key]
        elif self.default_language in self.translations and key in self.translations[self.default_language]:
            # Fallback to default language
            text = self.translations[self.default_language][key]
        else:
            # Use default or key itself
            text = default or key
        
        # Format with variables
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing variable in translation {key}: {e}")
        
        return text
    
    def get_plural(
        self,
        key: str,
        count: int,
        lang: str = "de",
        **kwargs
    ) -> str:
        """
        Get plural form
        
        Args:
            key: Translation key (e.g., "document_count")
            count: Number for pluralization
            lang: Language code
            **kwargs: Additional variables
        
        Returns:
            Pluralized string
        """
        
        # Determine plural form based on language rules
        if lang == "de":
            plural_key = f"{key}_one" if count == 1 else f"{key}_other"
        elif lang == "ru":
            # Russian has complex plural rules
            if count % 10 == 1 and count % 100 != 11:
                plural_key = f"{key}_one"
            elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
                plural_key = f"{key}_few"
            else:
                plural_key = f"{key}_many"
        else:  # English
            plural_key = f"{key}_one" if count == 1 else f"{key}_other"
        
        return self.get(plural_key, lang, count=count, **kwargs)
    
    def get_all(self, lang: str = "de") -> Dict:
        """Get all translations for a language"""
        
        return self.translations.get(lang, {})
    
    def add_translation(
        self,
        key: str,
        value: str,
        lang: str
    ):
        """
        Add or update translation
        
        Args:
            key: Translation key
            value: Translation value
            lang: Language code
        """
        
        if lang not in self.translations:
            self.translations[lang] = {}
        
        self.translations[lang][key] = value
        logger.info(f"Added translation: {lang}.{key}")


# Global locale manager
locale_manager = LocaleManager()
```

---

## ФАЙЛ 131: `locales/de.json`

```json
{
  "app_name": "IOS System",
  "welcome_message": "Willkommen im Information Operating System",
  "login": "Anmelden",
  "logout": "Abmelden",
  "username": "Benutzername",
  "password": "Passwort",
  
  "document": "Dokument",
  "documents": "Dokumente",
  "document_count_one": "{count} Dokument",
  "document_count_other": "{count} Dokumente",
  
  "search": "Suchen",
  "search_results": "Suchergebnisse",
  "no_results": "Keine Ergebnisse gefunden",
  
  "create": "Erstellen",
  "edit": "Bearbeiten",
  "delete": "Löschen",
  "save": "Speichern",
  "cancel": "Abbrechen",
  
  "personal_budget": "Persönliches Budget",
  "objection": "Widerspruch",
  "application": "Antrag",
  
  "error_occurred": "Ein Fehler ist aufgetreten",
  "success": "Erfolgreich",
  
  "loading": "Laden...",
  "processing": "Verarbeitung...",
  
  "language": "Sprache",
  "german": "Deutsch",
  "russian": "Russisch",
  "english": "Englisch"
}
```

---

## ФАЙЛ 132: `locales/ru.json`

```json
{
  "app_name": "Система IOS",
  "welcome_message": "Добро пожаловать в информационную операционную систему",
  "login": "Войти",
  "logout": "Выйти",
  "username": "Имя пользователя",
  "password": "Пароль",
  
  "document": "Документ",
  "documents": "Документы",
  "document_count_one": "{count} документ",
  "document_count_few": "{count} документа",
  "document_count_many": "{count} документов",
  
  "search": "Поиск",
  "search_results": "Результаты поиска",
  "no_results": "Результаты не найдены",
  
  "create": "Создать",
  "edit": "Редактировать",
  "delete": "Удалить",
  "save": "Сохранить",
  "cancel": "Отмена",
  
  "personal_budget": "Личный бюджет",
  "objection": "Возражение",
  "application": "Заявление",
  
  "error_occurred": "Произошла ошибка",
  "success": "Успешно",
  
  "loading": "Загрузка...",
  "processing": "Обработка...",
  
  "language": "Язык",
  "german": "Немецкий",
  "russian": "Русский",
  "english": "Английский"
}
```

---

## ФАЙЛ 133: `locales/en.json`

```json
{
  "app_name": "IOS System",
  "welcome_message": "Welcome to the Information Operating System",
  "login": "Login",
  "logout": "Logout",
  "username": "Username",
  "password": "Password",
  
  "document": "Document",
  "documents": "Documents",
  "document_count_one": "{count} document",
  "document_count_other": "{count} documents",
  
  "search": "Search",
  "search_results": "Search Results",
  "no_results": "No results found",
  
  "create": "Create",
  "edit": "Edit",
  "delete": "Delete",
  "save": "Save",
  "cancel": "Cancel",
  
  "personal_budget": "Personal Budget",
  "objection": "Objection",
  "application": "Application",
  
  "error_occurred": "An error occurred",
  "success": "Success",
  
  "loading": "Loading...",
  "processing": "Processing...",
  
  "language": "Language",
  "german": "German",
  "russian": "Russian",
  "english": "English"
}
```

---

## ФАЙЛ 134: `api/routes/i18n_api.py`

```python
"""
Internationalization API Routes
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ios_core.i18n.language_detector import language_detector
from ios_core.i18n.translator import translator
from ios_core.i18n.multilingual_processor import multilingual_processor
from ios_core.i18n.locale_manager import locale_manager
from ios_core.security.rbac import require_permission, Permission
from ..dependencies import get_current_user

router = APIRouter()


class DetectLanguageRequest(BaseModel):
    text: str
    hint: Optional[str] = None


class TranslateRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str


class ProcessDocumentRequest(BaseModel):
    document_id: str
    generate_translations: bool = False
    target_languages: Optional[List[str]] = None


class MultilingualSearchRequest(BaseModel):
    query: str
    query_language: Optional[str] = None
    search_languages: Optional[List[str]] = None
    limit: int = 10


@router.post("/detect-language")
async def detect_language(
    request: DetectLanguageRequest
):
    """
    Detect text language
    
    Uses ensemble of detection methods for accuracy.
    """
    
    try:
        result = language_detector.detect(
            text=request.text,
            hint=request.hint
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Language detection failed: {str(e)}"
        )


@router.post("/translate")
async def translate_text(
    request: TranslateRequest
):
    """
    Translate text
    
    Supports: de, ru, en
    """
    
    try:
        translated = await translator.translate(
            text=request.text,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
        
        return {
            "original": request.text,
            "translated": translated,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )


@router.post("/process-document")
@require_permission(Permission.DOCUMENT_UPDATE)
async def process_document_multilingual(
    request: ProcessDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process document for multilingual support
    
    - Detects language
    - Generates translations (optional)
    - Creates multilingual indexes
    
    Requires: DOCUMENT_UPDATE permission
    """
    
    try:
        # Process document
        result = await multilingual_processor.process_document(
            doc_id=request.document_id,
            generate_translations=request.generate_translations,
            target_languages=request.target_languages
        )
        
        # Create multilingual index
        if request.generate_translations:
            index_result = await multilingual_processor.create_multilingual_index(
                doc_id=request.document_id
            )
            result['indexing'] = index_result
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multilingual processing failed: {str(e)}"
        )


@router.post("/search-multilingual")
@require_permission(Permission.DOCUMENT_READ)
async def search_multilingual(
    request: MultilingualSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Search across multiple languages
    
    - Auto-detects query language
    - Translates query to target languages
    - Searches in all languages
    - Returns merged results
    
    Requires: DOCUMENT_READ permission
    """
    
    try:
        results = await multilingual_processor.search_multilingual(
            query=request.query,
            query_language=request.query_language,
            search_languages=request.search_languages,
            limit=request.limit
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multilingual search failed: {str(e)}"
        )


@router.get("/translations/{lang}")
async def get_translations(
    lang: str
):
    """
    Get UI translations for language
    
    Returns all translation strings for the specified language.
    """
    
    try:
        translations = locale_manager.get_all(lang=lang)
        
        if not translations:
            raise HTTPException(
                status_code=404,
                detail=f"Translations not found for language: {lang}"
            )
        
        return {
            "language": lang,
            "translations": translations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get translations: {str(e)}"
        )


@router.get("/supported-languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    
    return {
        "languages": [
            {
                "code": "de",
                "name": "Deutsch",
                "native_name": "Deutsch"
            },
            {
                "code": "ru",
                "name": "Russian",
                "native_name": "Русский"
            },
            {
                "code": "en",
                "name": "English",
                "native_name": "English"
            }
        ]
    }
```

---

**Продолжение следует...**

Создано:
- ✅ Language Detector (ensemble detection)
- ✅ Translator (multi-engine)
- ✅ Multilingual Processor
- ✅ Locale Manager
- ✅ Translation files (de, ru, en)
- ✅ API Routes

**Следующие файлы:**
- Performance optimization
- Tests
- Setup scripts
- Final documentation
- Week summary

**Готовы продолжить?**