# Run all tests
pytest -v --cov=ios_core --cov=api --cov-report=html

# Security scan
./scripts/security_scan.sh

# Performance test
locust -f tests/performance/load_test_suite.py \
  --host=https://staging.ios-system.com \
  --users=100 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=reports/final_load_test.html

# Build production images
docker build -t ios-system:1.0.0 -f docker/Dockerfile.production .

# Tag for registry
docker tag ios-system:1.0.0 ghcr.io/your-org/ios-system:1.0.0
docker tag ios-system:1.0.0 ghcr.io/your-org/ios-system:latest

# Push to registry
docker push ghcr.io/your-org/ios-system:1.0.0
docker push ghcr.io/your-org/ios-system:latest