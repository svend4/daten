"""
Tests for summarizer
"""

import pytest
from ios_core.gpt.summarizer import summarizer, SummaryLength, SummaryStyle


@pytest.mark.asyncio
async def test_summarize():
    """Test text summarization"""
    
    long_text = """Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe 
nach dem SGB IX. Es ermöglicht Menschen mit Behinderungen, ihre Unterstützungsleistungen 
selbstbestimmt zu organisieren und zu bezahlen. Anstelle von Sachleistungen erhalten 
Budgetnehmer eine Geldleistung, mit der sie die benötigten Hilfen eigenständig einkaufen 
können. Dies fördert die Selbstbestimmung und Teilhabe am Leben in der Gesellschaft."""
    
    result = await summarizer.summarize(
        text=long_text,
        length=SummaryLength.BRIEF,
        style=SummaryStyle.SIMPLE
    )
    
    assert "summary" in result
    assert len(result["summary"]) < len(long_text)
    assert result["compression_ratio"] < 1.0


@pytest.mark.asyncio
async def test_extract_key_points():
    """Test key point extraction"""
    
    text = """Das Widerspruchsverfahren ist ein wichtiger Rechtsbehelf.
Es muss innerhalb eines Monats eingelegt werden.
Der Widerspruch ist schriftlich oder zur Niederschrift einzureichen.
Eine Begründung kann nachgereicht werden.
Das Verfahren ist für den Antragsteller kostenlos."""
    
    result = await summarizer.extract_key_points(
        text=text,
        max_points=3
    )
    
    assert "key_points" in result
    assert len(result["key_points"]) <= 3