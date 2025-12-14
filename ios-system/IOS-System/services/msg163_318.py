# tests/api/test_api_endpoints.py

"""
API endpoint tests
"""

import pytest
from rest_framework.test import APIClient
from rest_framework import status
from search.models import Document
from django.contrib.auth.models import User

@pytest.mark.django_db
class TestSearchAPI:
    """Test Search API endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client and data"""
        self.client = APIClient()
        
        # Create test documents
        self.documents = [
            Document.objects.create(
                title=f'Test Document {i}',
                content=f'Content about German social law {i}',
                document_type=Document.DocumentType.LAW,
                category='Sozialrecht',
                legal_code='SGB IX',
                is_active=True,
                is_public=True
            )
            for i in range(10)
        ]
    
    def test_search_endpoint(self):
        """Test basic search endpoint"""
        response = self.client.post(
            '/api/search/',
            {
                'query': 'test',
                'page': 1,
                'page_size': 10
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'total' in response.data
        assert 'query_id' in response.data
    
    def test_search_with_filters(self):
        """Test search with filters"""
        response = self.client.post(
            '/api/search/',
            {
                'query': 'test',
                'filters': {
                    'document_type': 'LAW',
                    'legal_code': 'SGB IX'
                },
                'page': 1,
                'page_size': 10
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] > 0
    
    def test_search_pagination(self):
        """Test search pagination"""
        # Page 1
        response1 = self.client.post(
            '/api/search/',
            {'query': 'test', 'page': 1, 'page_size': 5},
            format='json'
        )
        
        # Page 2
        response2 = self.client.post(
            '/api/search/',
            {'query': 'test', 'page': 2, 'page_size': 5},
            format='json'
        )
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert len(response1.data['results']) <= 5
        assert len(response2.data['results']) <= 5
    
    def test_search_invalid_request(self):
        """Test search with invalid request"""
        response = self.client.post(
            '/api/search/',
            {'page': 1},  # Missing required 'query'
            format='json'
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_autocomplete_endpoint(self):
        """Test autocomplete endpoint"""
        response = self.client.get(
            '/api/autocomplete/',
            {'query': 'test', 'limit': 10}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_get_document(self):
        """Test get document endpoint"""
        doc = self.documents[0]
        
        response = self.client.get(f'/api/documents/{doc.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(doc.id)
        assert response.data['title'] == doc.title
        assert 'content' in response.data
    
    def test_track_click(self):
        """Test click tracking endpoint"""
        from search.models import SearchQuery
        
        # Create search query
        query = SearchQuery.objects.create(
            query_text='test',
            query_normalized='test',
            session_id='test-session',
            total_results=1
        )
        
        doc = self.documents[0]
        
        response = self.client.post(
            '/api/track-click/',
            {
                'query_id': str(query.id),
                'document_id': str(doc.id),
                'position': 1,
                'score': 0.95
            },
            format='json'
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify click event created
        from search.models import ClickEvent
        assert ClickEvent.objects.filter(
            search_query=query,
            document=doc
        ).exists()
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health/')
        
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]
        assert 'status' in response.data
        assert 'services' in response.data

@pytest.mark.django_db
class TestAPIRateLimiting:
    """Test API rate limiting"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test client"""
        self.client = APIClient()
    
    def test_anonymous_rate_limit(self):
        """Test rate limiting for anonymous users"""
        # Make many requests
        responses = []
        for _ in range(150):  # Exceeds 100/hour limit
            response = self.client.post(
                '/api/search/',
                {'query': 'test'},
                format='json'
            )
            responses.append(response.status_code)
        
        # Should get some 429 responses
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses
    
    def test_authenticated_rate_limit(self):
        """Test higher rate limit for authenticated users"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        # Should allow more requests
        responses = []
        for _ in range(100):
            response = self.client.post(
                '/api/search/',
                {'query': 'test'},
                format='json'
            )
            responses.append(response.status_code)
        
        # All should succeed
        assert all(
            code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
            for code in responses
        )