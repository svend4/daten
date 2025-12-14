# search/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from .models import Document, SearchQuery, UserPreference, ClickEvent

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for Document model"""
    
    list_display = [
        'title',
        'document_type',
        'legal_code',
        'paragraph',
        'is_active',
        'view_count',
        'click_count',
        'created_at'
    ]
    
    list_filter = [
        'document_type',
        'is_active',
        'is_public',
        'legal_code',
        'created_at',
        'embedding_generated'
    ]
    
    search_fields = [
        'title',
        'content',
        'legal_code',
        'paragraph',
        'tags'
    ]
    
    readonly_fields = [
        'id',
        'view_count',
        'click_count',
        'created_at',
        'updated_at',
        'embedding_status'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'content', 'summary', 'document_type', 'category')
        }),
        ('Legal Metadata', {
            'fields': ('legal_code', 'paragraph', 'version', 'effective_date')
        }),
        ('Source', {
            'fields': ('source_url', 'source_name', 'author')
        }),
        ('Status', {
            'fields': ('is_active', 'is_public', 'embedding_status')
        }),
        ('Statistics', {
            'fields': ('view_count', 'click_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Advanced', {
            'fields': ('id', 'tags'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_documents', 'deactivate_documents', 'regenerate_embeddings']
    
    def embedding_status(self, obj):
        """Display embedding generation status"""
        if obj.embedding_generated:
            return format_html(
                '<span style="color: green;">✓ Generated</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Pending</span>'
        )
    embedding_status.short_description = 'Embedding Status'
    
    def activate_documents(self, request, queryset):
        """Activate selected documents"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} documents activated.')
    activate_documents.short_description = 'Activate selected documents'
    
    def deactivate_documents(self, request, queryset):
        """Deactivate selected documents"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} documents deactivated.')
    deactivate_documents.short_description = 'Deactivate selected documents'
    
    def regenerate_embeddings(self, request, queryset):
        """Mark documents for embedding regeneration"""
        updated = queryset.update(embedding_generated=False)
        self.message_user(
            request,
            f'{updated} documents marked for embedding regeneration.'
        )
    regenerate_embeddings.short_description = 'Regenerate embeddings'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """Admin interface for SearchQuery model"""
    
    list_display = [
        'query_text',
        'user',
        'total_results',
        'search_time_ms',
        'search_type',
        'clicks_count',
        'created_at'
    ]
    
    list_filter = [
        'search_type',
        'created_at',
        ('user', admin.RelatedOnlyFieldListFilter)
    ]
    
    search_fields = [
        'query_text',
        'query_normalized',
        'session_id'
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'clicked_results_display'
    ]
    
    fieldsets = (
        ('Query Details', {
            'fields': ('query_text', 'query_normalized', 'search_type')
        }),
        ('User Context', {
            'fields': ('user', 'session_id', 'ip_address', 'user_agent')
        }),
        ('Search Parameters', {
            'fields': ('filters', 'sort_by', 'page', 'page_size')
        }),
        ('Results', {
            'fields': (
                'total_results',
                'results_returned',
                'clicked_results_display',
                'search_time_ms'
            )
        }),
        ('Meta', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def clicks_count(self, obj):
        """Count of clicked results"""
        return len(obj.clicked_results)
    clicks_count.short_description = 'Clicks'
    
    def clicked_results_display(self, obj):
        """Display clicked results"""
        if not obj.clicked_results:
            return 'No clicks'
        
        html = '<ul>'
        for click in obj.clicked_results:
            html += f"<li>Doc: {click['document_id']} (Position: {click['position']})</li>"
        html += '</ul>'
        return format_html(html)
    clicked_results_display.short_description = 'Clicked Results'


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    """Admin interface for UserPreference model"""
    
    list_display = [
        'user',
        'language_preference',
        'default_page_size',
        'history_count',
        'favorites_count',
        'updated_at'
    ]
    
    list_filter = [
        'language_preference',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'search_history_display'
    ]
    
    def history_count(self, obj):
        """Count of search history items"""
        return len(obj.search_history)
    history_count.short_description = 'History Items'
    
    def favorites_count(self, obj):
        """Count of favorite documents"""
        return obj.favorite_documents.count()
    favorites_count.short_description = 'Favorites'
    
    def search_history_display(self, obj):
        """Display recent search history"""
        if not obj.search_history:
            return 'No history'
        
        recent = obj.search_history[:10]
        return format_html('<br>'.join(recent))
    search_history_display.short_description = 'Recent Searches'


@admin.register(ClickEvent)
class ClickEventAdmin(admin.ModelAdmin):
    """Admin interface for ClickEvent model"""
    
    list_display = [
        'document_link',
        'query_text',
        'position',
        'score',
        'dwell_time_seconds',
        'clicked_at'
    ]
    
    list_filter = [
        'clicked_at',
        'position'
    ]
    
    search_fields = [
        'document__title',
        'search_query__query_text'
    ]
    
    readonly_fields = [
        'clicked_at',
        'document_link',
        'query_link'
    ]
    
    def document_link(self, obj):
        """Link to document"""
        url = reverse('admin:search_document_change', args=[obj.document.id])
        return format_html('<a href="{}">{}</a>', url, obj.document.title)
    document_link.short_description = 'Document'
    
    def query_text(self, obj):
        """Display query text"""
        return obj.search_query.query_text
    query_text.short_description = 'Query'
    
    def query_link(self, obj):
        """Link to search query"""
        url = reverse('admin:search_searchquery_change', args=[obj.search_query.id])
        return format_html('<a href="{}">{}</a>', url, obj.search_query.query_text)
    query_link.short_description = 'Query'


# Custom admin site configuration
admin.site.site_header = 'IOS Search System Administration'
admin.site.site_title = 'IOS Admin'
admin.site.index_title = 'Welcome to IOS Search System Administration'