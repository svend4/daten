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