# tests/unit/test_models.py

import pytest
from django.test import TestCase
from search.models import Document, SearchQuery, UserPreference
from django.contrib.auth.models import User
from datetime import date

@pytest.mark.django_db
class TestDocumentModel:
    """Test Document model"""
    
    def test_create_document(self):
        """Test creating a document"""
        doc = Document.objects.create(
            title='Test Document',
            content='This is test content',
            document_type=Document.DocumentType.LAW,
            category='Test Category',
            legal_code='SGB IX',
            paragraph='§ 1',
            is_active=True,
            is_public=True
        )
        
        assert doc.id is not None
        assert doc.title == 'Test Document'
        assert doc.view_count == 0
        assert doc.click_count == 0
    
    def test_increment_view_count(self):
        """Test incrementing view count"""
        doc = Document.objects.create(
            title='Test Document',
            content='Content',
            document_type=Document.DocumentType.LAW,
            category='Test'
        )
        
        initial_count = doc.view_count
        doc.increment_view_count()
        doc.refresh_from_db()
        
        assert doc.view_count == initial_count + 1
    
    def test_document_str_representation(self):
        """Test string representation"""
        doc = Document.objects.create(
            title='Test Document',
            content='Content',
            document_type=Document.DocumentType.LAW,
            category='Test'
        )
        
        expected = f"Test Document ({Document.DocumentType.LAW})"
        assert str(doc) == expected


@pytest.mark.django_db
class TestSearchQueryModel:
    """Test SearchQuery model"""
    
    def test_create_search_query(self):
        """Test creating a search query"""
        query = SearchQuery.objects.create(
            query_text='test query',
            query_normalized='test query',
            session_id='test-session',
            total_results=10,
            results_returned=10,
            search_time_ms=150
        )
        
        assert query.id is not None
        assert query.query_text == 'test query'
        assert query.search_time_ms == 150
    
    def test_add_clicked_result(self):
        """Test adding clicked result"""
        query = SearchQuery.objects.create(
            query_text='test',
            query_normalized='test',
            session_id='session'
        )
        
        doc_id = 'test-doc-id'
        position = 1
        
        query.add_clicked_result(doc_id, position)
        query.refresh_from_db()
        
        assert len(query.clicked_results) == 1
        assert query.clicked_results[0]['document_id'] == doc_id
        assert query.clicked_results[0]['position'] == position


@pytest.mark.django_db
class TestUserPreferenceModel:
    """Test UserPreference model"""
    
    def test_create_user_preference(self):
        """Test creating user preference"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        pref = UserPreference.objects.create(
            user=user,
            language_preference='de',
            default_page_size=20
        )
        
        assert pref.user == user
        assert pref.language_preference == 'de'
        assert len(pref.search_history) == 0
    
    def test_add_to_search_history(self):
        """Test adding to search history"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        pref = UserPreference.objects.create(user=user)
        
        pref.add_to_search_history('query 1')
        pref.add_to_search_history('query 2')
        
        assert len(pref.search_history) == 2
        assert pref.search_history[0] == 'query 2'  # Most recent first
        assert pref.search_history[1] == 'query 1'
    
    def test_search_history_limit(self):
        """Test search history respects max limit"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        pref = UserPreference.objects.create(user=user)
        
        # Add 60 queries
        for i in range(60):
            pref.add_to_search_history(f'query {i}')
        
        # Should only keep 50 (default max)
        assert len(pref.search_history) == 50