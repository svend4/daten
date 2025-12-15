"""
Tests for embedding service
"""

import pytest
from ios_core.ml.embeddings import embedding_service


@pytest.fixture
async def initialized_service():
    """Initialize embedding service"""
    await embedding_service.initialize()
    return embedding_service


@pytest.mark.asyncio
async def test_initialize(initialized_service):
    """Test service initialization"""
    
    assert initialized_service.initialized is True
    assert initialized_service.client is not None


@pytest.mark.asyncio
async def test_index_document(initialized_service):
    """Test document indexing"""
    
    success = await initialized_service.index_document(
        doc_id="test_doc_1",
        text="Dies ist ein Test-Dokument über das Persönliche Budget.",
        metadata={
            "domain_name": "SGB-IX",
            "title": "Test Document"
        }
    )
    
    assert success is True


@pytest.mark.asyncio
async def test_search_similar(initialized_service):
    """Test similarity search"""
    
    # First index a document
    await initialized_service.index_document(
        doc_id="test_doc_2",
        text="Das Persönliche Budget ist eine Leistungsform der Eingliederungshilfe.",
        metadata={"domain_name": "SGB-IX"}
    )
    
    # Search
    results = await initialized_service.search_similar(
        query="Persönliches Budget",
        limit=5,
        score_threshold=0.5
    )
    
    assert isinstance(results, list)
    
    if results:
        assert "id" in results[0]
        assert "score" in results[0]
        assert "text" in results[0]


@pytest.mark.asyncio
async def test_index_batch(initialized_service):
    """Test batch indexing"""
    
    documents = [
        {
            "id": f"batch_doc_{i}",
            "text": f"Test document {i} about SGB-IX regulations.",
            "metadata": {"domain_name": "SGB-IX"}
        }
        for i in range(5)
    ]
    
    stats = await initialized_service.index_batch(documents)
    
    assert stats["success"] == 5
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_get_similar_to_document(initialized_service):
    """Test finding similar documents"""
    
    # Index reference document
    doc_id = "ref_doc"
    await initialized_service.index_document(
        doc_id=doc_id,
        text="Widerspruch gegen den Bescheid des Bezirks Oberbayern.",
        metadata={"domain_name": "SGB-IX"}
    )
    
    # Index similar document
    await initialized_service.index_document(
        doc_id="similar_doc",
        text="Widerspruch gegen den Ablehnungsbescheid.",
        metadata={"domain_name": "SGB-IX"}
    )
    
    # Find similar
    results = await initialized_service.get_similar_to_document(
        doc_id=doc_id,
        limit=5
    )
    
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_delete_document(initialized_service):
    """Test document deletion"""
    
    doc_id = "delete_test"
    
    # Index
    await initialized_service.index_document(
        doc_id=doc_id,
        text="This will be deleted.",
        metadata={}
    )
    
    # Delete
    success = await initialized_service.delete_document(doc_id)
    assert success is True


@pytest.mark.asyncio
async def test_get_stats(initialized_service):
    """Test getting statistics"""
    
    stats = await initialized_service.get_stats()
    
    assert "total_documents" in stats
    assert "vector_dimension" in stats
    assert stats["vector_dimension"] == 1024