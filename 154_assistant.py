Отлично, пользователь хочет продолжить с детализацией фаз. Создам ФАЙЛ 19 с подробным разбором каждой фазы, включая:

1. Детальные технические задачи для каждого спринта
2. Примеры кода для каждой функции
3. Чеклисты для разработчиков
4. Тестовые сценарии
5. Критерии приемки
6. Распределение задач по разработчикам

Это будет практическое руководство для реализации проекта.# 🎯 DETAILED PHASE BREAKDOWN

## ФАЙЛ 19: `docs/PHASE_IMPLEMENTATION_DETAILS.md`

```markdown
# Phase Implementation Details - Детальная разбивка фаз

## 📘 PHASE 1: MVP - Детальный план

### Sprint 1: Infrastructure Setup (Week 1)

#### Task 1.1: Docker Environment Setup
**Assignee:** Backend Developer
**Time:** 1 day
**Priority:** Critical

```yaml
# docker-compose.dev.yml

version: '3.8'

services:
  # PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ios-postgres
    environment:
      POSTGRES_DB: ios_db
      POSTGRES_USER: ios_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ios_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: ios-elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - es_data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Qdrant
  qdrant:
    image: qdrant/qdrant:v1.7.0
    container_name: ios-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__GRPC_PORT=6334
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:6333/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    container_name: ios-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Django App (development)
  app:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: ios-app
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      elasticsearch:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://ios_user:${DB_PASSWORD}@postgres:5432/ios_db
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - QDRANT_URL=http://qdrant:6333
      - REDIS_URL=redis://redis:6379/0

volumes:
  postgres_data:
  es_data:
  qdrant_data:
  redis_data:
```

**Checklist:**
- [ ] Create `.env` file with secrets
- [ ] Test `docker-compose up -d`
- [ ] Verify all containers healthy
- [ ] Test connection to each service
- [ ] Document startup process

**Testing:**
```bash
# Test script: scripts/test-infrastructure.sh
#!/bin/bash

echo "Testing infrastructure..."

# Test PostgreSQL
docker exec ios-postgres pg_isready -U ios_user
if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL is ready"
else
    echo "✗ PostgreSQL failed"
    exit 1
fi

# Test Elasticsearch
curl -f http://localhost:9200/_cluster/health
if [ $? -eq 0 ]; then
    echo "✓ Elasticsearch is ready"
else
    echo "✗ Elasticsearch failed"
    exit 1
fi

# Test Qdrant
curl -f http://localhost:6333/health
if [ $? -eq 0 ]; then
    echo "✓ Qdrant is ready"
else
    echo "✗ Qdrant failed"
    exit 1
fi

# Test Redis
docker exec ios-redis redis-cli ping
if [ $? -eq 0 ]; then
    echo "✓ Redis is ready"
else
    echo "✗ Redis failed"
    exit 1
fi

echo "All services are healthy!"
```

---

#### Task 1.2: Django Settings Configuration
**Assignee:** Backend Developer
**Time:** 1 day
**Priority:** Critical

```python
# ios_core/settings/base.py

"""
Base settings for IOS project
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',  # Swagger documentation
    'django_filters',
    'corsheaders',
    
    # Local apps
    'search.apps.SearchConfig',
    'analytics.apps.AnalyticsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ios_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ios_core.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'ios_db'),
        'USER': os.environ.get('DB_USER', 'ios_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    }
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# Elasticsearch
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200'),
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True,
    }
}

# Qdrant
QDRANT_CONFIG = {
    'host': os.environ.get('QDRANT_HOST', 'localhost'),
    'port': int(os.environ.get('QDRANT_PORT', 6333)),
    'grpc_port': int(os.environ.get('QDRANT_GRPC_PORT', 6334)),
    'prefer_grpc': True,
    'timeout': 30,
}

# Redis
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'ios',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'ios.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'search': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Search Configuration
SEARCH_CONFIG = {
    'elasticsearch': {
        'index_name': 'ios-documents',
        'max_results': 100,
        'default_page_size': 20,
    },
    'qdrant': {
        'collection_name': 'ios-vectors',
        'vector_size': 384,  # multilingual-e5-small
        'distance': 'Cosine',
    },
    'fusion': {
        'algorithm': 'rrf',  # reciprocal_rank_fusion
        'k': 60,  # RRF parameter
        'weights': {
            'elasticsearch': 0.5,
            'qdrant': 0.5,
        }
    },
    'embedding': {
        'model': 'sentence-transformers/multilingual-e5-small',
        'batch_size': 32,
        'cache_embeddings': True,
    }
}
```

```python
# ios_core/settings/development.py

from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Disable some security for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Enable CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
INTERNAL_IPS = ['127.0.0.1']

# Detailed logging
LOGGING['root']['level'] = 'DEBUG'
```

```python
# ios_core/settings/production.py

from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files (use WhiteNoise or S3)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Database - enable connection pooling
DATABASES['default']['CONN_MAX_AGE'] = 600
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 seconds
}

# Caching - longer TTL
CACHES['default']['TIMEOUT'] = 3600  # 1 hour

# Logging - less verbose
LOGGING['root']['level'] = 'INFO'
```

**Checklist:**
- [ ] Create settings split (base, dev, prod)
- [ ] Configure all external services
- [ ] Setup logging
- [ ] Configure caching
- [ ] Test settings in docker
- [ ] Document configuration options

---

#### Task 1.3: Database Models
**Assignee:** Backend Developer
**Time:** 2 days
**Priority:** Critical

```python
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
```

**Database Migration:**
```bash
python manage.py makemigrations
python manage.py migrate
```

**Seed Data Script:**
```python
# scripts/seed_data.py

"""
Seed database with sample data
"""

from django.core.management.base import BaseCommand
from search.models import Document
from datetime import date

class Command(BaseCommand):
    help = 'Seed database with sample documents'
    
    def handle(self, *args, **options):
        documents = [
            {
                'title': 'SGB IX § 29 - Persönliches Budget',
                'content': '''
                    Das Persönliche Budget ist eine alternative Leistungsform,
                    bei der Menschen mit Behinderungen anstelle von Sach- oder
                    Dienstleistungen ein Budget zur Verfügung gestellt wird...
                ''',
                'document_type': Document.DocumentType.LAW,
                'category': 'Sozialrecht',
                'legal_code': 'SGB IX',
                'paragraph': '§ 29',
                'effective_date': date(2020, 1, 1),
                'is_active': True,
                'is_public': True,
            },
            # Add more sample documents...
        ]
        
        for doc_data in documents:
            doc, created = Document.objects.get_or_create(
                title=doc_data['title'],
                defaults=doc_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created: {doc.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Seeding completed!')
        )
```

**Checklist:**
- [ ] Create all models
- [ ] Add proper indexes
- [ ] Create migrations
- [ ] Test migrations
- [ ] Create seed data
- [ ] Test model methods
- [ ] Add admin interface

---

**Продолжить с Task 1.4: CI/CD Setup?**