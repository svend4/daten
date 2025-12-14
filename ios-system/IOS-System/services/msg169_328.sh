# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# All tests with coverage
pytest --cov=search --cov-report=html

# Load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000