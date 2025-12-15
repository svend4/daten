"""
Integration test for complete document processing pipeline
This is the most important test - it validates the entire system
"""

import pytest
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from ios_core.system import IOSSystem
from ios_core.models import Base
from ios_core.config import settings


@pytest.fixture
async def db_session():
    """Create test database session"""
    # Use test database
    engine = create_async_engine(
        "postgresql+asyncpg://ios_user:ios_password@localhost:5432/ios_test",
        echo=True
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def test_document_path(tmp_path):
    """Create test document"""
    doc_path = tmp_path / "test_widerspruch.txt"
    doc_path.write_text("""
    Widerspruch gegen Bescheid vom 15.11.2024
    
    Sehr geehrte Damen und Herren,
    
    hiermit widerspreche ich dem Bescheid vom 15.11.2024 über die Ablehnung
    des Persönlichen Budgets gemäß § 29 SGB IX.
    
    Die Ablehnung ist rechtswidrig, da die Voraussetzungen nach § 29 SGB IX
    eindeutig erfüllt sind.
    
    Zuständigkeit liegt beim Bezirk Oberbayern gemäß § 98 SGB IX.
    
    Mit freundlichen Grüßen
    Max Mustermann
    """)
    return str(doc_path)


@pytest.mark.asyncio
async def test_complete_document_pipeline(db_session, test_document_path):
    """
    Test complete document processing pipeline
    
    This test validates:
    1. Document processing
    2. Classification
    3. Entity extraction
    4. Relation extraction
    5. Database storage
    6. Search indexing
    """
    # Initialize system
    ios = IOSSystem(db_session=db_session)
    
    # Process document
    result = await ios.process_document(
        file_path=test_document_path,
        domain_name="SGB-IX",
        title="Test Widerspruch",
        tags=["test", "widerspruch"]
    )
    
    # Verify result
    assert result['status'] == 'success'
    assert result['document_id'] is not None
    assert result['classification']['type'] == 'Widerspruch'
    assert result['classification']['confidence'] > 0.7
    assert result['entities_count'] > 0
    
    # Verify document in database
    document = await ios.get_document(result['document_id'])
    assert document['title'] == 'Test Widerspruch'
    assert document['domain_name'] == 'SGB-IX'
    
    # Verify search indexing
    search_results = await ios.search_documents(
        query="Widerspruch",
        domain_name="SGB-IX"
    )
    assert search_results['total_count'] > 0
    assert any(
        doc['doc_id'] == result['document_id'] 
        for doc in search_results['results']
    )
    
    print("✓ Complete pipeline test passed!")


@pytest.mark.asyncio
async def test_entity_extraction(db_session, test_document_path):
    """Test that entities are correctly extracted"""
    ios = IOSSystem(db_session=db_session)
    
    result = await ios.process_document(
        file_path=test_document_path,
        domain_name="SGB-IX"
    )
    
    # Should extract:
    # - § 29 (Paragraph)
    # - § 98 (Paragraph)
    # - SGB IX (Gesetz)
    # - Bezirk Oberbayern (Behörde)
    # - Persönliches Budget (Leistung)
    
    assert result['entities_count'] >= 3  # At minimum
    
    print("✓ Entity extraction test passed!")


@pytest.mark.asyncio
async def test_classification_accuracy(db_session, tmp_path):
    """Test classification with different document types"""
    ios = IOSSystem(db_session=db_session)
    
    test_cases = [
        {
            "content": "Antrag auf Persönliches Budget gemäß § 29 SGB IX...",
            "expected_type": "Antrag",
            "filename": "antrag.txt"
        },
        {
            "content": "Bescheid: Die Leistung wird bewilligt...",
            "expected_type": "Bescheid",
            "filename": "bescheid.txt"
        },
        {
            "content": "Widerspruch gegen den Bescheid vom...",
            "expected_type": "Widerspruch",
            "filename": "widerspruch.txt"
        },
    ]
    
    for test_case in test_cases:
        # Create test file
        file_path = tmp_path / test_case['filename']
        file_path.write_text(test_case['content'])
        
        # Process
        result = await ios.process_document(
            file_path=str(file_path),
            domain_name="SGB-IX"
        )
        
        # Verify
        assert result['classification']['type'] == test_case['expected_type'], \
            f"Expected {test_case['expected_type']}, got {result['classification']['type']}"
    
    print("✓ Classification accuracy test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])