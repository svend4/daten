# Run performance tests again
locust -f tests/performance/test_load.py

# Metrics should improve:
# Before optimization:
# - Average response: 800ms
# - 95th percentile: 1500ms
# - Throughput: 50 req/s

# After optimization:
# - Average response: <300ms ✓
# - 95th percentile: <600ms ✓
# - Throughput: >150 req/s ✓

# Cache hit rate
redis-cli INFO stats | grep keyspace_hits
# Target: >80% hit rate for search queries