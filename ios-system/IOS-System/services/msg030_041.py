# tests/unit/test_classification.py

import pytest
from ios_core.services.classifier import ClassificationService, FeatureExtractor
from ios_core.models import Document


@pytest.fixture
def classifier():
    return ClassificationService()


def test_classify_widerspruch(classifier):
    """Test Widerspruch classification"""
    doc = Document(
        id="test1",
        title="Widerspruch",
        content="""
        Widerspruch gegen Bescheid vom 15.11.2024
        
        Sehr geehrte Damen und Herren,
        hiermit widerspreche ich dem Bescheid.
        
        Mit freundlichen Grüßen
        """,
        file_path="",
        creation_date=None
    )
    
    result = await classifier.classify(doc)
    
    assert result.document_type == "Widerspruch"
    assert result.confidence > 0.8


def test_feature_extraction():
    """Test feature extraction"""
    extractor = FeatureExtractor()
    
    content = "Gemäß § 29 SGB IX beantrage ich..."
    features = extractor.extract(Document(
        id="test",
        content=content,
        title="",
        file_path="",
        creation_date=None
    ))
    
    assert '§29' in features['entities']
    assert any('sgb' in e.lower() for e in features['entities'])