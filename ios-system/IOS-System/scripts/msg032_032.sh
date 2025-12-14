# Install locust
pip install locust

# Run load test
locust -f tests/performance/test_load.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# Set users: 50
# Spawn rate: 10/s
# Run for 5 minutes

# Target metrics:
# - Average response time: <500ms
# - 95th percentile: <1000ms
# - Error rate: <1%
# - Throughput: >100 req/s