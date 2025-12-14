"""
Tests for document generator
"""

import pytest
from ios_core.gpt.document_generator import document_generator


@pytest.mark.asyncio
async def test_generate_objection():
    """Test objection letter generation"""
    
    case_details = {
        "applicant_name": "Max Mustermann",
        "decision_date": "2024-01-15",
        "case_number": "AB-123-2024",
        "reason": "Unzureichende Begründung des Ablehnungsbescheids"
    }
    
    result = await document_generator.generate_objection(
        case_details=case_details
    )
    
    assert "document_id" in result
    assert "content" in result
    assert "Max Mustermann" in result["content"]
    assert "Widerspruch" in result["content"]


@pytest.mark.asyncio
async def test_generate_application():
    """Test application generation"""
    
    applicant_info = {
        "name": "Maria Schmidt",
        "address": "Musterstraße 1, 80331 München",
        "birth_date": "1990-05-15"
    }
    
    result = await document_generator.generate_application(
        benefit_type="Persönliches Budget",
        applicant_info=applicant_info,
        justification="Ich benötige Unterstützung zur selbstbestimmten Lebensführung."
    )
    
    assert "document_id" in result
    assert "content" in result
    assert "Persönliches Budget" in result["content"]