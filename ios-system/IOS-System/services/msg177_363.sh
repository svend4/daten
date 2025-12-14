# 1. Создать тестовые данные
python manage.py shell

>>> from search.services.elasticsearch_service import ElasticsearchService
>>> es = ElasticsearchService()
>>> es.create_index()  # Создать индекс
>>> # Проверить что работает

# 2. Запустить unit tests
pytest tests/unit/test_elasticsearch_service.py -v
pytest tests/unit/test_qdrant_service.py -v
pytest tests/unit/test_hybrid_search.py -v