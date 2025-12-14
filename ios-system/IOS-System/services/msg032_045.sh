# API tests
pytest tests/api/ -v

# Should have:
# - test_auth.py (login, register, token validation)
# - test_documents.py (upload, get, list, delete)
# - test_search.py (search, autocomplete)
# - test_rate_limiting.py (rate limit enforcement)

# All tests passing