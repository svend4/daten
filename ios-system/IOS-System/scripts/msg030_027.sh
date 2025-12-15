# Run all tests
pytest -v

# Should show:
# - Unit tests: ~15 passing
# - Integration tests: ~3 passing

# Code coverage
pytest --cov=ios_core --cov-report=html
# Target: >60% coverage