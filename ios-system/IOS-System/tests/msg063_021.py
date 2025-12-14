"""
Tests for language detector
"""

import pytest
from ios_core.i18n.language_detector import language_detector


def test_detect_german():
    """Test German detection"""
    
    result = language_detector.detect(
        "Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe."
    )
    
    assert result['language'] == 'de'
    assert result['confidence'] > 0.8


def test_detect_russian():
    """Test Russian detection"""
    
    result = language_detector.detect(
        "Личный бюджет для людей с ограниченными возможностями."
    )
    
    assert result['language'] == 'ru'
    assert result['confidence'] > 0.8


def test_detect_english():
    """Test English detection"""
    
    result = language_detector.detect(
        "Personal budget for people with disabilities."
    )
    
    assert result['language'] == 'en'
    assert result['confidence'] > 0.6


def test_detect_with_umlauts():
    """Test German detection with umlauts"""
    
    result = language_detector.detect("Äpfel, Öl, Übung")
    
    assert result['language'] == 'de'


def test_detect_cyrillic():
    """Test Cyrillic script detection"""
    
    result = language_detector.detect("Привет мир")
    
    assert result['language'] == 'ru'


def test_detect_multiple_languages():
    """Test mixed language detection"""
    
    results = language_detector.detect_multiple(
        "Hello, wie geht's? Привет!"
    )
    
    assert len(results) > 0
    languages = [r[0] for r in results]
    
    # Should detect at least 2 languages
    assert len(set(languages)) >= 2