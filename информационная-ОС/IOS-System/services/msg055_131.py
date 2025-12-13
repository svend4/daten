"""
Tests for neural search
"""

import pytest
from ios_core.search.neural_search import neural_search
from ios_core.search.query_understanding import query_analyzer
from ios_core.search.multi_language import multi_language, Language


@pytest.mark.asyncio
async def test_neural_search():
    """Test neural search execution"""
    
    results = await neural_search.search(
        query="Persönliches Budget",
        limit=10,
        language="de"
    )
    
    assert "query" in results
    assert "results" in results
    assert "total" in results
    assert "execution_time_ms" in results
    assert results["query"] == "Persönliches Budget"


@pytest.mark.asyncio
async def test_query_analysis():
    """Test query understanding"""
    
    query_info = await query_analyzer.analyze(
        query="Wie beantrage ich ein Persönliches Budget?",
        language="de"
    )
    
    assert "language" in query_info
    assert "intent" in query_info
    assert "is_question" in query_info
    assert query_info["is_question"] is True


@pytest.mark.asyncio
async def test_language_detection():
    """Test language detection"""
    
    # German
    lang_de = multi_language.detect_language("Das Persönliche Budget")
    assert lang_de == Language.GERMAN
    
    # Russian
    lang_ru = multi_language.detect_language("Личный бюджет для инвалидов")
    assert lang_ru == Language.RUSSIAN
    
    # English
    lang_en = multi_language.detect_language("Personal budget for disabled persons")
    assert lang_en == Language.ENGLISH


@pytest.mark.asyncio
async def test_query_translation():
    """Test query translation"""
    
    translated = await multi_language.translate_query(
        query="Personal budget",
        source_lang=Language.ENGLISH,
        target_lang=Language.GERMAN
    )
    
    assert isinstance(translated, str)
    assert len(translated) > 0


@pytest.mark.asyncio
async def test_legal_reference_extraction():
    """Test legal reference extraction"""
    
    query_info = await query_analyzer.analyze(
        query="§ 29 SGB IX Persönliches Budget",
        language="de"
    )
    
    assert "legal_references" in query_info
    assert len(query_info["legal_references"]) > 0
    assert any("§ 29" in ref for ref in query_info["legal_references"])


@pytest.mark.asyncio
async def test_entity_extraction():
    """Test entity extraction from query"""
    
    query_info = await query_analyzer.analyze(
        query="Antrag beim Bezirk Oberbayern stellen",
        language="de"
    )
    
    assert "entities" in query_info
    # May or may not find entities depending on BERT model


@pytest.mark.asyncio
async def test_query_expansion():
    """Test query expansion"""
    
    query_info = await query_analyzer.analyze(
        query="Persönliches Budget",
        language="de"
    )
    
    assert "expansion" in query_info
    # Expansions should include synonyms


@pytest.mark.asyncio
async def test_suggestions():
    """Test query suggestions"""
    
    suggestions = await neural_search.suggest(
        query="Pers",
        limit=5,
        language="de"
    )
    
    assert isinstance(suggestions, list)