# Написать базовые тесты
# tests/unit/test_classifier.py

import pytest
from ios_system.classifier import ClassificationEngine

@pytest.fixture
def classifier():
    return ClassificationEngine()

def test_classify_widerspruch(classifier):
    doc = Document(
        title="Widerspruch gegen Bescheid",
        content="Hiermit widerspreche ich dem Bescheid..."
    )
    
    classification = classifier.classify(doc)
    
    assert classification.document_type == "Widerspruch"
    assert classification.confidence > 0.8

def test_extract_entities_paragraph(classifier):
    doc = Document(
        content="Gemäß § 29 SGB IX haben Sie Anspruch..."
    )
    
    features = classifier.feature_extractor.extract(doc)
    
    assert "§29" in [e.name for e in features['entities']]
    assert "SGB-IX" in [e.name for e in features['entities']]

# tests/integration/test_document_pipeline.py

@pytest.mark.asyncio
async def test_complete_document_pipeline():
    ios = IOSSystem(config)
    await ios.initialize()
    
    # Upload document
    doc, classification, entities = await ios.add_document(
        "test_data/widerspruch.pdf",
        "SGB-IX"
    )
    
    # Verify classification
    assert classification.document_type == "Widerspruch"
    
    # Verify entities extracted
    assert len(entities) > 0
    
    # Verify indexed
    results = await ios.search_engine.search("Widerspruch")
    assert doc.id in [r['doc_id'] for r in results['results']]