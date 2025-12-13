# Run edge case tests
pytest tests/edge_cases/ -v

# All should pass or handle gracefully
# No crashes, no data corruption

# Performance check after fixes
pytest tests/performance/ --benchmark-only