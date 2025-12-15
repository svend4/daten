# Test 1: Normal load
locust -f tests/performance/load_test_suite.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=5m \
  --html=reports/load_test_normal.html

# Test 2: Stress test
locust -f tests/performance/load_test_suite.py \
  --host=http://localhost:8000 \
  --users=200 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=reports/load_test_stress.html

# Test 3: Spike test
locust -f tests/performance/load_test_suite.py \
  --host=http://localhost:8000 \
  --users=500 \
  --spawn-rate=50 \
  --run-time=2m \
  --html=reports/load_test_spike.html

# Analyze results
python scripts/analyze_performance.py reports/