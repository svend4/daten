# Запустить тесты
pytest tests/search/test_elasticsearch.py -v

# Benchmark
python scripts/benchmark_search.py

# Expected improvement:
# Elasticsearch 2-3x faster than Whoosh
# Better relevance
# More features