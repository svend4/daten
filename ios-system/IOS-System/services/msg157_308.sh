#!/bin/bash
# scripts/run-integration-tests.sh

echo "Starting integration test environment..."

# Start services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
echo "Waiting for services..."
sleep 30

# Run tests
docker-compose -f docker-compose.test.yml run --rm app-test

# Capture exit code
TEST_EXIT_CODE=$?

# Cleanup
echo "Cleaning up..."
docker-compose -f docker-compose.test.yml down -v

exit $TEST_EXIT_CODE