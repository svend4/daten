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