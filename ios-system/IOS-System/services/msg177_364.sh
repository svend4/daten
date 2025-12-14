# 1. Запустить сервер
python manage.py runserver

# 2. Открыть Swagger
# http://localhost:8000/swagger/

# 3. Протестировать endpoints
curl -X POST http://localhost:8000/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "page": 1}'

# 4. Запустить API tests
pytest tests/integration/test_api.py -v