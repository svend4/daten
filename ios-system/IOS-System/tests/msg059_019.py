"""
Tests for QA system
"""

import pytest
from ios_core.gpt.qa_system import qa_system


@pytest.mark.asyncio
async def test_answer_question():
    """Test question answering"""
    
    result = await qa_system.answer(
        question="Was ist ein Persönliches Budget?",
        max_context_docs=3
    )
    
    assert "question" in result
    assert "answer" in result
    assert "confidence" in result
    assert "sources" in result
    assert result["confidence"] in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_explain_concept():
    """Test concept explanation"""
    
    result = await qa_system.explain_concept(
        concept="Eingliederungshilfe",
        detail_level="simple"
    )
    
    assert "concept" in result
    assert "explanation" in result
    assert "Eingliederungshilfe" in result["explanation"]