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