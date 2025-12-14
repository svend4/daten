# tests/integration/test_edge_cases.py

@pytest.mark.asyncio
async def test_large_document_processing():
    """Test processing very large documents"""
    
    # Create 10MB document
    large_content = "Test content. " * 1000000
    
    # Should handle without timeout or memory issues
    result = await ios.process_document(...)
    
    assert result['status'] == 'success'


@pytest.mark.asyncio  
async def test_concurrent_uploads():
    """Test concurrent document uploads"""
    
    tasks = [
        ios.process_document(f"doc_{i}.txt", "Test")
        for i in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    
    # All should succeed
    assert all(r['status'] == 'success' for r in results)


@pytest.mark.asyncio
async def test_special_characters():
    """Test documents with special characters"""
    
    doc_with_special_chars = """
    Special characters: äöü ß é è à
    Symbols: § © ® ™
    Math: ∑ ∫ √ π
    """
    
    result = await ios.process_document(...)
    assert result['status'] == 'success'