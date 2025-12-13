# search/models.py

"""
Database models for search application
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
import uuid

class Document(models.Model):
    """
    Main document model for searchable content
    """
    
    class DocumentType(models.TextChoices):
        LAW = 'LAW', _('Gesetz')
        REGULATION = 'REG', _('Verordnung')
        COURT_DECISION = 'COURT', _('Gerichtsentscheidung')
        GUIDELINE = 'GUIDE', _('Richtlinie')
        TEMPLATE = 'TEMPLATE', _('Vorlage')
        ARTICLE = 'ARTICLE', _('Artikel')
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=500, db_index=True)
    content = models.TextField()
    summary = models.TextField(blank=True)
    
    # Classification
    document_type = models.CharField(
        max_length=10,
        choices=DocumentType.choices,
        db_index=True
    )
    category = models.CharField(max_length=100, db_index=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Legal metadata
    legal_code = models.CharField(max_length=20, blank=True, db_index=True)  # e.g., "SGB IX"
    paragraph = models.CharField(max_length=50, blank=True)  # e.g., "§ 29"
    version = models.CharField(max_length=50, blank=True)
    effective_date = models.DateField(null=True, blank=True)
    
    # Search optimization
    search_vector = models.TextField(blank=True)  # Pre-computed search text
    embedding_generated = models.BooleanField(default=False, db_index=True)
    
    # Source information
    source_url = models.URLField(max_length=1000, blank=True)
    source_name = models.CharField(max_length=200, blank=True)
    author = models.CharField(max_length=200, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_public = models.BooleanField(default=True)
    
    # Statistics
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['document_type', 'is_active']),
            models.Index(fields=['legal_code', 'paragraph']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['embedding_generated', 'is_active']),
        ]
        verbose_name = _('Dokument')
        verbose_name_plural = _('Dokumente')
    
    def __str__(self):
        return f"{self.title} ({self.document_type})"
    
    def increment_view_count(self):
        """Increment view counter"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])
    
    def increment_click_count(self):
        """Increment click counter"""
        self.click_count = models.F('click_count') + 1
        self.save(update_fields=['click_count'])


class SearchQuery(models.Model):
    """
    Track search queries for analytics
    """
    
    # Query details
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    query_text = models.CharField(max_length=500, db_index=True)
    query_normalized = models.CharField(max_length=500, db_index=True)
    
    # User context
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries'
    )
    session_id = models.CharField(max_length=100, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    
    # Search parameters
    filters = models.JSONField(default=dict, blank=True)
    sort_by = models.CharField(max_length=50, blank=True)
    page = models.PositiveIntegerField(default=1)
    page_size = models.PositiveIntegerField(default=20)
    
    # Results
    total_results = models.PositiveIntegerField(default=0)
    results_returned = models.PositiveIntegerField(default=0)
    clicked_results = models.JSONField(default=list, blank=True)  # List of clicked doc IDs
    
    # Performance
    search_time_ms = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    # Source
    search_type = models.CharField(
        max_length=20,
        choices=[
            ('hybrid', 'Hybrid Search'),
            ('elasticsearch', 'Elasticsearch Only'),
            ('qdrant', 'Vector Search Only'),
            ('autocomplete', 'Autocomplete'),
        ],
        default='hybrid'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'search_queries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query_text', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['session_id', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        verbose_name = _('Suchabfrage')
        verbose_name_plural = _('Suchabfragen')
    
    def __str__(self):
        return f"{self.query_text} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    def add_clicked_result(self, document_id: str, position: int):
        """Record that a result was clicked"""
        self.clicked_results.append({
            'document_id': str(document_id),
            'position': position,
            'clicked_at': timezone.now().isoformat()
        })
        self.save(update_fields=['clicked_results'])


class UserPreference(models.Model):
    """
    User preferences for personalization
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='search_preference'
    )
    
    # Preferences
    preferred_document_types = models.JSONField(default=list, blank=True)
    preferred_categories = models.JSONField(default=list, blank=True)
    language_preference = models.CharField(max_length=10, default='de')
    
    # Search settings
    default_page_size = models.PositiveIntegerField(
        default=20,
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )
    default_sort = models.CharField(max_length=50, default='relevance')
    
    # Behavior tracking
    search_history = models.JSONField(default=list, blank=True)  # Recent queries
    favorite_documents = models.ManyToManyField(
        Document,
        blank=True,
        related_name='favorited_by'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('Benutzerpräferenz')
        verbose_name_plural = _('Benutzerpräferenzen')
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def add_to_search_history(self, query: str, max_items: int = 50):
        """Add query to search history"""
        if query not in self.search_history:
            self.search_history.insert(0, query)
            self.search_history = self.search_history[:max_items]
            self.save(update_fields=['search_history'])


class ClickEvent(models.Model):
    """
    Track click events for Learning to Rank
    """
    
    search_query = models.ForeignKey(
        SearchQuery,
        on_delete=models.CASCADE,
        related_name='click_events'
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='click_events'
    )
    
    # Click details
    position = models.PositiveIntegerField()  # Position in search results
    score = models.FloatField(null=True, blank=True)  # Search score
    
    # Dwell time (how long user stayed on document)
    dwell_time_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Timestamp
    clicked_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'click_events'
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['search_query', 'document']),
            models.Index(fields=['document', '-clicked_at']),
        ]
        verbose_name = _('Click Event')
        verbose_name_plural = _('Click Events')
    
    def __str__(self):
        return f"Click on {self.document.title} at position {self.position}"