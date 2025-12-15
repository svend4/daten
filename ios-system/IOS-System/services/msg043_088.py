"""
Tests for Elasticsearch service
"""

import pytest
from datetime import datetime

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.models import DocumentModel


@pytest.fixture
async def es_service():
    """Elasticsearch service fixture"""
    
    es = ElasticsearchService()
    await es.initialize()
    
    yield es
    
    # Cleanup
    await es.client.indices.delete(index=es.index_name, ignore=[404])
    await es.close()


@pytest.mark.asyncio
async def test_index_document(es_service, sample_document):
    """Test document indexing"""
    
    success = await es_service.index_document(sample_document)
    
    assert success
    
    # Verify document is indexed
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    response = await es_service.client.get(
        index=es_service.index_name,
        id=sample_document.id
    )
    
    assert response["_source"]["title"] == sample_document.title


@pytest.mark.asyncio
async def test_bm25_search(es_service, sample_documents):
    """Test BM25 search"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Search
    results = await es_service.search(
        query="Widerspruch",
        search_type="bm25",
        limit=10
    )
    
    assert results["total"] > 0
    assert len(results["results"]) > 0
    assert results["results"][0]["score"] > 0


@pytest.mark.asyncio
async def test_filtered_search(es_service, sample_documents):
    """Test search with filters"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Search with domain filter
    results = await es_service.search(
        query="test",
        domain_name="SGB-IX",
        search_type="bm25"
    )
    
    assert all(r["domain_name"] == "SGB-IX" for r in results["results"])


@pytest.mark.asyncio
async def test_aggregation(es_service, sample_documents):
    """Test aggregations"""
    
    # Index documents
    for doc in sample_documents:
        await es_service.index_document(doc)
    
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Aggregate by document type
    agg_results = await es_service.aggregate(field="document_type")
    
    assert len(agg_results) > 0
    assert all("key" in r and "count" in r for r in agg_results)


@pytest.mark.asyncio
async def test_bulk_index(es_service, sample_documents):
    """Test bulk indexing"""
    
    stats = await es_service.bulk_index(sample_documents)
    
    assert stats["success"] == len(sample_documents)
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_document(es_service, sample_document):
    """Test document deletion"""
    
    # Index document
    await es_service.index_document(sample_document)
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    # Delete
    success = await es_service.delete_document(sample_document.id)
    
    assert success
    
    # Verify deleted
    await es_service.client.indices.refresh(index=es_service.index_name)
    
    from elasticsearch import NotFoundError
    with pytest.raises(NotFoundError):
        await es_service.client.get(
            index=es_service.index_name,
            id=sample_document.id
        )