Пользователь хочет продолжить с Task 1.4: CI/CD Setup. Продолжу детальную разбивку фазы MVP.## ФАЙЛ 19 (продолжение): CI/CD Setup и дальнейшие задачи

```markdown
# Phase Implementation Details (продолжение)

#### Task 1.4: CI/CD Pipeline Setup
**Assignee:** DevOps/Backend Developer
**Time:** 1 day
**Priority:** High

```yaml
# .github/workflows/ci.yml

name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

env:
  PYTHON_VERSION: '3.11'
  POETRY_VERSION: '1.7.0'

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: test_ios_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: |
            ~/.cache/pypoetry
            ~/.cache/pip
          key: ${{ runner.os }}-poetry-${{ hashFiles('**/poetry.lock') }}
          restore-keys: |
            ${{ runner.os }}-poetry-
      
      - name: Install Poetry
        run: |
          curl -sSL https://install.python-poetry.org | python3 -
          echo "$HOME/.local/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: |
          poetry install --no-interaction --no-ansi
      
      - name: Run linting
        run: |
          poetry run flake8 .
          poetry run black --check .
          poetry run isort --check-only .
      
      - name: Run type checking
        run: |
          poetry run mypy .
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_ios_db
          REDIS_URL: redis://localhost:6379/0
          DJANGO_SETTINGS_MODULE: ios_core.settings.test
        run: |
          poetry run pytest \
            --cov=search \
            --cov=analytics \
            --cov-report=xml \
            --cov-report=html \
            --cov-report=term-missing \
            --junitxml=junit.xml \
            -v
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: |
            junit.xml
            htmlcov/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          pip install safety bandit
      
      - name: Run safety check
        run: |
          safety check --json
      
      - name: Run bandit security scan
        run: |
          bandit -r . -f json -o bandit-report.json
      
      - name: Upload security reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json

  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ios/search-api
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=ios/search-api:buildcache
          cache-to: type=registry,ref=ios/search-api:buildcache,mode=max
      
      - name: Image digest
        run: echo ${{ steps.meta.outputs.digest }}

  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.ios-search.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to staging
        env:
          DEPLOY_KEY: ${{ secrets.STAGING_DEPLOY_KEY }}
          STAGING_HOST: ${{ secrets.STAGING_HOST }}
        run: |
          # SSH to staging server and pull latest image
          echo "$DEPLOY_KEY" | ssh-add -
          ssh $STAGING_HOST "cd /opt/ios && docker-compose pull && docker-compose up -d"
      
      - name: Run health check
        run: |
          curl -f https://staging.ios-search.com/health/ || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://ios-search.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.PRODUCTION_DEPLOY_KEY }}
          PRODUCTION_HOST: ${{ secrets.PRODUCTION_HOST }}
        run: |
          # Blue-green deployment strategy
          echo "$DEPLOY_KEY" | ssh-add -
          ssh $PRODUCTION_HOST "cd /opt/ios && ./scripts/deploy.sh"
      
      - name: Run smoke tests
        run: |
          curl -f https://ios-search.com/health/ || exit 1
          curl -f https://ios-search.com/api/search/?query=test || exit 1
      
      - name: Notify team
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Production deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

```yaml
# .github/workflows/nightly-tests.yml

name: Nightly Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Run at 2 AM UTC daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Compose
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30  # Wait for services to start
      
      - name: Run integration tests
        run: |
          docker-compose -f docker-compose.test.yml exec -T app \
            pytest tests/integration/ -v
      
      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v

  load-tests:
    name: Load Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up environment
        run: |
          docker-compose -f docker-compose.test.yml up -d
          sleep 30
      
      - name: Run load tests
        run: |
          pip install locust
          locust -f tests/load/locustfile.py \
            --headless \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --host http://localhost:8000 \
            --html load-test-report.html
      
      - name: Upload load test report
        uses: actions/upload-artifact@v3
        with:
          name: load-test-report
          path: load-test-report.html
      
      - name: Cleanup
        if: always()
        run: |
          docker-compose -f docker-compose.test.yml down -v
```

**Pre-commit Hooks:**

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: debug-statements
  
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

**Test Configuration:**

```python
# ios_core/settings/test.py

from .base import *

DEBUG = True

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'test_ios_db'),
        'USER': os.environ.get('DATABASE_USER', 'test_user'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'test_password'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}

# Use in-memory cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Disable Elasticsearch/Qdrant for unit tests
ELASTICSEARCH_DSL['default']['hosts'] = []
QDRANT_CONFIG['host'] = 'localhost'

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for tests (use --keepdb for faster runs)
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# MIGRATION_MODULES = DisableMigrations()

# Test-specific logging
LOGGING['root']['level'] = 'WARNING'
```

```ini
# pytest.ini

[pytest]
DJANGO_SETTINGS_MODULE = ios_core.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --reuse-db
    --nomigrations
    --cov=search
    --cov=analytics
    --cov-report=term-missing:skip-covered
    --cov-report=html
    --cov-report=xml
    --junit-xml=junit.xml
    -ra
    -q
testpaths = tests
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    elasticsearch: requires Elasticsearch
    qdrant: requires Qdrant
```

**Sample Tests:**

```python
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
```

**Checklist:**
- [ ] Create CI/CD workflow files
- [ ] Setup GitHub Actions
- [ ] Configure secrets
- [ ] Add pre-commit hooks
- [ ] Write test configuration
- [ ] Create sample unit tests
- [ ] Test CI pipeline
- [ ] Document CI/CD process

---

### Sprint 2: Database & Testing (Week 2)

#### Task 2.1: Complete Database Setup
**Assignee:** Backend Developer
**Time:** 1 day
**Priority:** Critical

**Admin Interface:**

```python
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
```

**Data Migration Script:**

```python
# search/management/commands/import_documents.py

from django.core.management.base import BaseCommand
from search.models import Document
import json
import csv
from pathlib import Path

class Command(BaseCommand):
    help = 'Import documents from JSON or CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to JSON or CSV file'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='File format'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk creation'
        )
    
    def handle(self, *args, **options):
        file_path = Path(options['file_path'])
        file_format = options['format']
        batch_size = options['batch_size']
        
        if not file_path.exists():
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
            return
        
        if file_format == 'json':
            self.import_from_json(file_path, batch_size)
        else:
            self.import_from_csv(file_path, batch_size)
    
    def import_from_json(self, file_path, batch_size):
        """Import from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        documents = []
        for item in data:
            doc = Document(
                title=item['title'],
                content=item['content'],
                document_type=item.get('document_type', 'ARTICLE'),
                category=item.get('category', 'General'),
                legal_code=item.get('legal_code', ''),
                paragraph=item.get('paragraph', ''),
                tags=item.get('tags', []),
                is_active=True,
                is_public=True
            )
            documents.append(doc)
            
            if len(documents) >= batch_size:
                Document.objects.bulk_create(documents, ignore_conflicts=True)
                self.stdout.write(f'Imported {len(documents)} documents')
                documents = []
        
        # Import remaining
        if documents:
            Document.objects.bulk_create(documents, ignore_conflicts=True)
            self.stdout.write(f'Imported {len(documents)} documents')
        
        self.stdout.write(
            self.style.SUCCESS('Import completed!')
        )
    
    def import_from_csv(self, file_path, batch_size):
        """Import from CSV file"""
        documents = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                doc = Document(
                    title=row['title'],
                    content=row['content'],
                    document_type=row.get('type', 'ARTICLE'),
                    category=row.get('category', 'General'),
                    legal_code=row.get('legal_code', ''),
                    is_active=True
                )
                documents.append(doc)
                
                if len(documents) >= batch_size:
                    Document.objects.bulk_create(documents, ignore_conflicts=True)
                    self.stdout.write(f'Imported {len(documents)} documents')
                    documents = []
        
        if documents:
            Document.objects.bulk_create(documents, ignore_conflicts=True)
            self.stdout.write(f'Imported {len(documents)} documents')
        
        self.stdout.write(
            self.style.SUCCESS('Import completed!')
        )
```

**Checklist:**
- [ ] Configure Django admin
- [ ] Create custom admin actions
- [ ] Add import/export commands
- [ ] Test admin interface
- [ ] Create sample data
- [ ] Verify all CRUD operations

---

**Продолжить с Task 2.2: Integration Testing?**