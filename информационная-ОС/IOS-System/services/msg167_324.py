# tests/qa/test_smoke.py

"""
Smoke tests for critical functionality
Run these after every deployment
"""

import pytest
from rest_framework.test import APIClient
from django.core.cache import cache

@pytest.mark.smoke
@pytest.mark.django_db
class TestSmokeSuite:
    """
    Smoke tests to verify system is functional
    
    These tests check critical paths and should run quickly
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        self.client = APIClient()
        cache.clear()
    
    def test_health_check(self):
        """System health check responds"""
        response = self.client.get('/api/health/')
        assert response.status_code in [200, 503]
        assert 'status' in response.data
    
    def test_search_basic_functionality(self):
        """Basic search works"""
        response = self.client.post(
            '/api/search/',
            {'query': 'test', 'page': 1},
            format='json'
        )
        assert response.status_code == 200
        assert 'results' in response.data
    
    def test_autocomplete_works(self):
        """Autocomplete responds"""
        response = self.client.get('/api/autocomplete/?query=test')
        assert response.status_code == 200
    
    def test_api_documentation_accessible(self):
        """API docs are accessible"""
        response = self.client.get('/swagger/')
        assert response.status_code == 200
    
    def test_admin_accessible(self):
        """Admin interface loads"""
        response = self.client.get('/admin/')
        # Should redirect to login or show login page
        assert response.status_code in [200, 302]

@pytest.mark.qa
@pytest.mark.django_db
class TestEndToEndScenarios:
    """
    End-to-end test scenarios
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        self.client = APIClient()
    
    def test_complete_search_flow(self):
        """
        Test complete search flow:
        1. Search
        2. Get document
        3. Track click
        """
        # 1. Search
        search_response = self.client.post(
            '/api/search/',
            {'query': 'test', 'page': 1},
            format='json'
        )
        assert search_response.status_code == 200
        
        query_id = search_response.data.get('query_id')
        results = search_response.data.get('results', [])
        
        if not results:
            pytest.skip("No results to test with")
        
        # 2. Get first document
        doc_id = results[0]['id']
        doc_response = self.client.get(f'/api/documents/{doc_id}/')
        assert doc_response.status_code == 200
        
        # 3. Track click
        click_response = self.client.post(
            '/api/track-click/',
            {
                'query_id': query_id,
                'document_id': doc_id,
                'position': 1
            },
            format='json'
        )
        assert click_response.status_code == 201
    
    def test_search_with_all_features(self):
        """
        Test search with all features enabled:
        - Filters
        - Sorting
        - Pagination
        """
        response = self.client.post(
            '/api/search/',
            {
                'query': 'test',
                'filters': {
                    'document_type': 'LAW'
                },
                'sort_by': 'date_desc',
                'page': 1,
                'page_size': 10
            },
            format='json'
        )
        
        assert response.status_code == 200
        assert response.data['page'] == 1
        assert response.data['page_size'] == 10