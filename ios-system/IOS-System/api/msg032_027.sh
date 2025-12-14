# Run all API tests
pytest tests/api/ -v --cov=api

# Coverage should be >70% for API code

# Manual testing with Postman/Insomnia
# Import OpenAPI spec from http://localhost:8000/api/openapi.json