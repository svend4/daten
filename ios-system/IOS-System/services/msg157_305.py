# tests/integration/test_qdrant_integration.py

"""
Integration tests for Qdrant vector search
"""

import pytest
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import numpy as np

@pytest.mark.integration
@pytest.mark.qdrant
class TestQdrantIntegration:
    """Test Qdrant integration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup Qdrant for tests"""
        self.client = QdrantClient(host='localhost', port=6333)
        self.collection_name = 'test-ios-vectors'
        
        # Delete collection if exists
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except:
            pass
        
        # Create collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        
        yield
        
        # Cleanup
        try:
            self.client.delete_collection(collection_name=self.collection_name)
        except:
            pass
    
    def test_insert_vectors(self):
        """Test inserting vectors"""
        # Create sample vectors
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(10)
        ]
        
        # Insert points
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={'title': f'Document {i}'}
            )
            for i, vec in enumerate(vectors)
        ]
        
        result = self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        assert result.status == 'completed'
        
        # Verify count
        info = self.client.get_collection(collection_name=self.collection_name)
        assert info.points_count == 10
    
    def test_similarity_search(self):
        """Test similarity search"""
        # Insert vectors
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(100)
        ]
        
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={
                    'title': f'Document {i}',
                    'legal_code': f'SGB {(i % 3) + 1}'
                }
            )
            for i, vec in enumerate(vectors)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Search with query vector
        query_vector = np.random.rand(384).tolist()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10
        )
        
        assert len(results) == 10
        assert all(hasattr(r, 'score') for r in results)
        assert all(0 <= r.score <= 1 for r in results)
    
    def test_filtered_search(self):
        """Test search with payload filters"""
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Insert vectors with metadata
        vectors = [
            np.random.rand(384).tolist()
            for _ in range(50)
        ]
        
        points = [
            PointStruct(
                id=i,
                vector=vec,
                payload={
                    'title': f'Document {i}',
                    'document_type': 'LAW' if i % 2 == 0 else 'COURT',
                    'legal_code': 'SGB IX'
                }
            )
            for i, vec in enumerate(vectors)
        ]
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        # Search with filter
        query_vector = np.random.rand(384).tolist()
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key='document_type',
                        match=MatchValue(value='LAW')
                    )
                ]
            ),
            limit=10
        )
        
        assert len(results) <= 10
        assert all(r.payload['document_type'] == 'LAW' for r in results)
    
    def test_batch_upload_performance(self):
        """Test batch upload performance"""
        import time
        
        # Generate 10,000 vectors
        batch_size = 1000
        total_vectors = 10000
        
        start = time.time()
        
        for batch_start in range(0, total_vectors, batch_size):
            batch_end = min(batch_start + batch_size, total_vectors)
            
            vectors = [
                np.random.rand(384).tolist()
                for _ in range(batch_end - batch_start)
            ]
            
            points = [
                PointStruct(
                    id=batch_start + i,
                    vector=vec,
                    payload={'doc_id': batch_start + i}
                )
                for i, vec in enumerate(vectors)
            ]
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 30.0  # Less than 30 seconds
        
        # Verify count
        info = self.client.get_collection(collection_name=self.collection_name)
        assert info.points_count == total_vectors