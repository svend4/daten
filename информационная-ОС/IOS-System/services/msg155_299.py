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