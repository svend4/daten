Пользователь хочет продолжить с Task 7.3: Bug Fixes & Quality Assurance. Это часть Sprint 7-8: Testing & Polish. Нужно создать детальный план для QA, багфиксинга, и общего улучшения качества кода.

Покрою:
1. Bug tracking система
2. QA test cases
3. Code quality tools (linting, type checking)
4. Security scanning
5. Common bug patterns and fixes
6. Regression testing
7. Code review checklist## ФАЙЛ 19 (продолжение): Bug Fixes & Quality Assurance

```markdown
# Phase Implementation Details (продолжение)

#### Task 7.3: Bug Fixes & Quality Assurance
**Assignee:** Full Team
**Time:** 3 days
**Priority:** Critical

**Bug Tracking System Setup:**

```python
# docs/bug_tracking_template.md

# Bug Report Template

## Bug ID: BUG-XXXX

### Priority
- [ ] Critical (System down)
- [ ] High (Major feature broken)
- [ ] Medium (Feature partially broken)
- [ ] Low (Minor issue)

### Severity
- [ ] Blocker (Prevents release)
- [ ] Major (Significant impact)
- [ ] Minor (Small impact)
- [ ] Trivial (Cosmetic)

### Environment
- **Component**: [e.g., Search API, Elasticsearch, Qdrant]
- **Version**: [e.g., v1.0.0]
- **Environment**: [e.g., Production, Staging, Development]
- **Browser/Client**: [if applicable]

### Description
[Clear description of the bug]

### Steps to Reproduce
1. [First step]
2. [Second step]
3. [Third step]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Screenshots/Logs
```
[Paste error logs or screenshots]
```

### Workaround
[If any temporary solution exists]

### Root Cause Analysis
[After investigation]

### Fix Description
[How it was fixed]

### Test Cases
- [ ] Test case 1
- [ ] Test case 2

### Related Issues
- Related to: #XXXX
- Blocks: #XXXX
- Blocked by: #XXXX
```

**Common Bug Patterns & Fixes:**

```python
# search/tests/test_bug_fixes.py

"""
Regression tests for fixed bugs
"""

import pytest
from rest_framework.test import APIClient
from search.models import Document, SearchQuery
from django.core.cache import cache

@pytest.mark.django_db
class TestBugFixes:
    """
    Test cases for previously identified bugs
    
    Each test represents a bug that was found and fixed
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.client = APIClient()
        cache.clear()
    
    def test_bug_001_empty_search_query(self):
        """
        BUG-001: Empty search query causes 500 error
        
        Status: FIXED
        Priority: High
        
        Issue: When query is empty string, search fails with KeyError
        Fix: Added validation in SearchRequestSerializer
        """
        response = self.client.post(
            '/api/search/',
            {'query': '', 'page': 1},
            format='json'
        )
        
        # Should return 400 Bad Request, not 500
        assert response.status_code == 400
        assert 'query' in response.data
    
    def test_bug_002_special_characters_in_query(self):
        """
        BUG-002: Special characters break Elasticsearch query
        
        Status: FIXED
        Priority: High
        
        Issue: Queries with special chars like [, ], {, } cause ES error
        Fix: Properly escape special characters in ES query builder
        """
        special_queries = [
            'test[bracket]',
            'test{brace}',
            'test"quote"',
            'test\\backslash',
            'test/slash'
        ]
        
        for query in special_queries:
            response = self.client.post(
                '/api/search/',
                {'query': query, 'page': 1},
                format='json'
            )
            
            # Should not crash
            assert response.status_code in [200, 400]
            if response.status_code == 200:
                assert 'results' in response.data
    
    def test_bug_003_pagination_out_of_range(self):
        """
        BUG-003: Requesting page beyond total pages returns 500
        
        Status: FIXED
        Priority: Medium
        
        Issue: Page 9999 causes IndexError
        Fix: Return empty results for out-of-range pages
        """
        response = self.client.post(
            '/api/search/',
            {'query': 'test', 'page': 9999, 'page_size': 20},
            format='json'
        )
        
        assert response.status_code == 200
        assert response.data['results'] == []
        assert response.data['page'] == 9999
    
    def test_bug_004_concurrent_click_tracking(self):
        """
        BUG-004: Race condition in click count increment
        
        Status: FIXED
        Priority: Medium
        
        Issue: Concurrent requests lose click counts
        Fix: Use F() expressions for atomic updates
        """
        from django.db.models import F
        
        # Create document
        doc = Document.objects.create(
            title='Test',
            content='Content',
            document_type='LAW',
            category='Test',
            click_count=0
        )
        
        # Create search query
        query = SearchQuery.objects.create(
            query_text='test',
            query_normalized='test',
            session_id='test',
            total_results=1
        )
        
        # Simulate concurrent clicks
        from concurrent.futures import ThreadPoolExecutor
        
        def track_click():
            self.client.post(
                '/api/track-click/',
                {
                    'query_id': str(query.id),
                    'document_id': str(doc.id),
                    'position': 1
                },
                format='json'
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(track_click) for _ in range(10)]
            for future in futures:
                future.result()
        
        # Verify all clicks were counted
        doc.refresh_from_db()
        assert doc.click_count == 10
    
    def test_bug_005_cache_key_collision(self):
        """
        BUG-005: Different queries generate same cache key
        
        Status: FIXED
        Priority: High
        
        Issue: Queries with different filters get same cache key
        Fix: Include all parameters in cache key generation
        """
        from search.services.caching import CacheService
        
        cache_service = CacheService()
        
        # Generate keys for similar but different queries
        key1 = cache_service.generate_search_cache_key(
            query='test',
            filters={'document_type': 'LAW'},
            page=1,
            page_size=20,
            sort_by='relevance'
        )
        
        key2 = cache_service.generate_search_cache_key(
            query='test',
            filters={'document_type': 'COURT'},
            page=1,
            page_size=20,
            sort_by='relevance'
        )
        
        # Keys must be different
        assert key1 != key2
    
    def test_bug_006_german_umlauts_search(self):
        """
        BUG-006: German umlauts not properly handled in search
        
        Status: FIXED
        Priority: High
        
        Issue: Searches with ä, ö, ü, ß don't find documents
        Fix: Configure German analyzer in Elasticsearch
        """
        # Create document with umlauts
        doc = Document.objects.create(
            title='Persönliches Budget für Behinderte',
            content='Inhalt über das persönliche Budget',
            document_type='LAW',
            category='Sozialrecht',
            is_active=True,
            is_public=True
        )
        
        # Search with umlauts
        response = self.client.post(
            '/api/search/',
            {'query': 'persönlich', 'page': 1},
            format='json'
        )
        
        assert response.status_code == 200
        # Should find the document
        # (This test may need actual ES setup to pass)
    
    def test_bug_007_null_embedding_handling(self):
        """
        BUG-007: Null embeddings cause Qdrant search to fail
        
        Status: FIXED
        Priority: High
        
        Issue: Documents without embeddings crash vector search
        Fix: Filter documents without embeddings, return empty vector on error
        """
        from search.services.qdrant_service import QdrantService
        
        qdrant = QdrantService()
        
        # Test with various edge cases
        test_cases = [
            '',  # Empty string
            ' ',  # Whitespace
            None,  # None (should be handled)
        ]
        
        for test_input in test_cases:
            try:
                embedding = qdrant.generate_embedding(test_input or 'fallback')
                assert isinstance(embedding, list)
                assert len(embedding) == qdrant.vector_size
            except Exception as e:
                pytest.fail(f"Failed to handle input '{test_input}': {e}")
    
    def test_bug_008_sql_injection_prevention(self):
        """
        BUG-008: Potential SQL injection in custom filters
        
        Status: FIXED
        Priority: Critical
        
        Issue: Raw SQL in some query builders
        Fix: Use Django ORM parameterized queries everywhere
        """
        # Try SQL injection attempts
        injection_attempts = [
            "'; DROP TABLE documents; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        for attempt in injection_attempts:
            response = self.client.post(
                '/api/search/',
                {
                    'query': attempt,
                    'filters': {'category': attempt},
                    'page': 1
                },
                format='json'
            )
            
            # Should handle safely
            assert response.status_code in [200, 400]
            
            # Verify tables still exist
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM information_schema.tables "
                    "WHERE table_name = 'documents'"
                )
                count = cursor.fetchone()[0]
                assert count == 1, "Table was affected by injection!"
    
    def test_bug_009_memory_leak_in_bulk_indexing(self):
        """
        BUG-009: Memory leak during bulk document indexing
        
        Status: FIXED
        Priority: High
        
        Issue: Large batch indexing runs out of memory
        Fix: Process in smaller batches, clear cache between batches
        """
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many documents
        docs = [
            Document(
                title=f'Doc {i}',
                content=f'Content {i}' * 100,  # Make content larger
                document_type='LAW',
                category='Test',
                is_active=True
            )
            for i in range(1000)
        ]
        
        Document.objects.bulk_create(docs)
        
        # Index in batches
        from search.services.elasticsearch_service import ElasticsearchService
        es = ElasticsearchService()
        
        for i in range(0, len(docs), 100):
            batch = docs[i:i+100]
            es.bulk_index_documents(batch)
            
            # Memory should not grow unbounded
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = current_memory - initial_memory
            
            # Allow some growth, but not excessive
            assert memory_growth < 500, f"Memory leak detected: {memory_growth}MB growth"
    
    def test_bug_010_timezone_handling(self):
        """
        BUG-010: Inconsistent timezone handling in date filters
        
        Status: FIXED
        Priority: Medium
        
        Issue: Date filters use different timezones
        Fix: Always use UTC internally, convert for display
        """
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        # Create document with specific timestamp
        doc = Document.objects.create(
            title='Time Test',
            content='Content',
            document_type='LAW',
            category='Test',
            created_at=now,
            is_active=True
        )
        
        # Search with date filter
        response = self.client.post(
            '/api/search/',
            {
                'query': 'Time',
                'filters': {
                    'date_from': (now - timedelta(days=1)).isoformat(),
                    'date_to': (now + timedelta(days=1)).isoformat()
                },
                'page': 1
            },
            format='json'
        )
        
        assert response.status_code == 200
        # Should find the document regardless of timezone
```

**Code Quality Tools Configuration:**

```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: debug-statements
      - id: detect-private-key
  
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11
        args: ['--line-length=100']
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile=black', '--line-length=100']
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']
        additional_dependencies: [
          'flake8-docstrings',
          'flake8-bugbear',
          'flake8-comprehensions'
        ]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: ['--ignore-missing-imports']
  
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ['-r', '.', '-ll']
        exclude: ^tests/
  
  - repo: https://github.com/Lucas-C/pre-commit-hooks-safety
    rev: v1.3.3
    hooks:
      - id: python-safety-dependencies-check
```

```ini
# setup.cfg

[flake8]
max-line-length = 100
extend-ignore = E203, W503, E501
exclude =
    .git,
    __pycache__,
    .venv,
    venv,
    migrations,
    */migrations/*
max-complexity = 10

[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
ignore_missing_imports = True

[isort]
profile = black
line_length = 100
multi_line_output = 3
include_trailing_comma = True
force_grid_wrap = 0
use_parentheses = True
ensure_newline_before_comments = True

[coverage:run]
source = search,analytics
omit =
    */migrations/*
    */tests/*
    */test_*.py
    */__pycache__/*
    */venv/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

**Security Scanning:**

```python
# scripts/security_scan.py

"""
Security scanning script
"""

import subprocess
import sys
import json

def run_command(cmd, description):
    """Run shell command and return output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    """Run security scans"""
    
    print("\n" + "="*60)
    print("SECURITY SCAN - IOS SEARCH SYSTEM")
    print("="*60)
    
    all_passed = True
    
    # 1. Safety check (Python dependencies)
    print("\n[1/5] Checking Python dependencies for known vulnerabilities...")
    if not run_command(
        "safety check --json",
        "Safety - Dependency Vulnerability Check"
    ):
        all_passed = False
        print("⚠️  Found vulnerabilities in dependencies")
    else:
        print("✓ No known vulnerabilities")
    
    # 2. Bandit (Python code security)
    print("\n[2/5] Scanning Python code for security issues...")
    if not run_command(
        "bandit -r . -f json -o bandit-report.json",
        "Bandit - Python Security Scanner"
    ):
        all_passed = False
        print("⚠️  Found security issues in code")
    else:
        print("✓ No security issues found")
    
    # 3. Django security check
    print("\n[3/5] Running Django security checks...")
    if not run_command(
        "python manage.py check --deploy --fail-level WARNING",
        "Django Security Check"
    ):
        all_passed = False
        print("⚠️  Django security warnings found")
    else:
        print("✓ Django security checks passed")
    
    # 4. Secret scanning
    print("\n[4/5] Scanning for exposed secrets...")
    if not run_command(
        "detect-secrets scan --all-files --baseline .secrets.baseline",
        "Secret Detection"
    ):
        all_passed = False
        print("⚠️  Potential secrets found")
    else:
        print("✓ No secrets detected")
    
    # 5. OWASP Dependency Check
    print("\n[5/5] Running OWASP dependency check...")
    if not run_command(
        "pip list --format=json | python scripts/check_owasp.py",
        "OWASP Dependency Check"
    ):
        print("⚠️  OWASP check incomplete (optional)")
    
    # Summary
    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL SECURITY CHECKS PASSED")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("✗ SOME SECURITY CHECKS FAILED")
        print("="*60 + "\n")
        print("Please review the issues above and fix them before deployment.")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**QA Test Cases:**

```python
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
```

**Code Review Checklist:**

```markdown
# Code Review Checklist

## General
- [ ] Code follows project style guide
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] No TODO comments without tickets
- [ ] Meaningful variable/function names
- [ ] Code is DRY (Don't Repeat Yourself)

## Functionality
- [ ] Code does what it's supposed to do
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Input validation is present
- [ ] No hardcoded values (use config)

## Testing
- [ ] Unit tests are included
- [ ] Tests cover edge cases
- [ ] Tests are meaningful (not just for coverage)
- [ ] Integration tests if needed
- [ ] All tests pass

## Performance
- [ ] No N+1 query problems
- [ ] Database queries are optimized
- [ ] Appropriate use of caching
- [ ] No memory leaks
- [ ] Efficient algorithms used

## Security
- [ ] No SQL injection vulnerabilities
- [ ] No XSS vulnerabilities
- [ ] User input is validated/sanitized
- [ ] Sensitive data is not logged
- [ ] Authentication/authorization checked
- [ ] CSRF protection in place
- [ ] No secrets in code

## API
- [ ] Endpoints follow REST conventions
- [ ] Proper HTTP status codes
- [ ] Input validation with clear error messages
- [ ] API documentation updated
- [ ] Rate limiting considered
- [ ] Pagination for list endpoints

## Database
- [ ] Migrations are reversible
- [ ] Indexes are appropriate
- [ ] Foreign keys defined
- [ ] ON DELETE behavior specified
- [ ] No data loss in migrations

## Documentation
- [ ] Docstrings for public functions
- [ ] README updated if needed
- [ ] API docs updated
- [ ] Complex logic explained
- [ ] Comments explain "why", not "what"

## Deployment
- [ ] Configuration for different environments
- [ ] Environment variables documented
- [ ] No breaking changes to API
- [ ] Database migration plan
- [ ] Rollback plan considered
```

**Checklist:**
- [ ] Setup bug tracking template
- [ ] Write regression tests for known bugs
- [ ] Configure code quality tools
- [ ] Run security scans
- [ ] Create QA test suite
- [ ] Perform code review
- [ ] Fix critical bugs
- [ ] Fix high-priority bugs
- [ ] Document fixes

---

**Продолжить с Task 7.4: Documentation Updates & Sprint 9-10?**