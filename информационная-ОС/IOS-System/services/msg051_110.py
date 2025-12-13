"""
Tests for BERT client
"""

import pytest
from ios_core.ml.bert_client import BERTClient


@pytest.mark.asyncio
async def test_bert_health_check():
    """Test BERT service health check"""
    
    client = BERTClient()
    health = await client.health_check()
    
    assert health["status"] in ["healthy", "unhealthy"]
    
    if health["status"] == "healthy":
        assert "model" in health
        assert health["models_loaded"]["embedding"] is True


@pytest.mark.asyncio
async def test_embed_single():
    """Test single text embedding"""
    
    client = BERTClient()
    
    text = "Das Persönliche Budget nach § 29 SGB IX"
    embedding = await client.embed_single(text)
    
    assert isinstance(embedding, list)
    assert len(embedding) == 1024  # GBERT-large dimension
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_embed_batch():
    """Test batch embedding"""
    
    client = BERTClient()
    
    texts = [
        "Widerspruch gegen den Bescheid",
        "Antrag auf Persönliches Budget",
        "Klage vor dem Sozialgericht"
    ]
    
    embeddings = await client.embed(texts)
    
    assert len(embeddings) == 3
    assert all(len(emb) == 1024 for emb in embeddings)


@pytest.mark.asyncio
async def test_extract_entities():
    """Test named entity recognition"""
    
    client = BERTClient()
    
    text = "Max Mustermann beantragt beim Bezirk Oberbayern ein Persönliches Budget."
    
    entities = await client.extract_entities(text, threshold=0.5)
    
    assert isinstance(entities, list)
    
    # Check for expected entities
    entity_types = {ent["entity"] for ent in entities}
    assert "PER" in entity_types or "MISC" in entity_types or "ORG" in entity_types


@pytest.mark.asyncio
async def test_compute_similarity():
    """Test similarity computation"""
    
    client = BERTClient()
    
    text1 = "Antrag auf Persönliches Budget"
    text2 = "Bewilligung des Persönlichen Budgets"
    text3 = "Wettervorhersage für München"
    
    # Similar texts
    sim_high = await client.compute_similarity(text1, text2)
    assert sim_high > 0.6  # Should be similar
    
    # Dissimilar texts
    sim_low = await client.compute_similarity(text1, text3)
    assert sim_low < 0.5  # Should be dissimilar


@pytest.mark.asyncio
async def test_normalize_embeddings():
    """Test embedding normalization"""
    
    client = BERTClient()
    
    text = "Test text"
    
    # Get normalized embedding
    emb_norm = await client.embed_single(text, normalize=True)
    
    # Check if normalized (unit length)
    import numpy as np
    norm = np.linalg.norm(emb_norm)
    assert abs(norm - 1.0) < 0.01  # Should be ~1.0
    
    # Get unnormalized embedding
    emb_unnorm = await client.embed_single(text, normalize=False)
    unnorm = np.linalg.norm(emb_unnorm)
    
    # Unnormalized should have different length
    assert abs(unnorm - 1.0) > 0.1