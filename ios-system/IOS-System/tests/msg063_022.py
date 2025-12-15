"""
Tests for translator
"""

import pytest
from ios_core.i18n.translator import translator


@pytest.mark.asyncio
async def test_translate_en_to_de():
    """Test English to German translation"""
    
    result = await translator.translate(
        text="Personal budget",
        source_lang="en",
        target_lang="de"
    )
    
    assert isinstance(result, str)
    assert len(result) > 0
    # Should contain "Budget" or similar
    assert "budget" in result.lower() or "бюджет" in result.lower()


@pytest.mark.asyncio
async def test_translate_same_language():
    """Test translation with same source and target"""
    
    text = "Test text"
    result = await translator.translate(
        text=text,
        source_lang="en",
        target_lang="en"
    )
    
    assert result == text


@pytest.mark.asyncio
async def test_translate_batch():
    """Test batch translation"""
    
    texts = [
        "Hello",
        "World",
        "Test"
    ]
    
    results = await translator.translate_batch(
        texts=texts,
        source_lang="en",
        target_lang="de"
    )
    
    assert len(results) == len(texts)
    assert all(isinstance(r, str) for r in results)


@pytest.mark.asyncio
async def test_cache():
    """Test translation caching"""
    
    text = "Unique test text for caching"
    
    # First translation
    result1 = await translator.translate(
        text=text,
        source_lang="en",
        target_lang="de"
    )
    
    # Second translation (should use cache)
    result2 = await translator.translate(
        text=text,
        source_lang="en",
        target_lang="de"
    )
    
    assert result1 == result2