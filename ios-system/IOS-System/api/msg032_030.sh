# Run all tests
pytest -v --cov=ios_core --cov=api --cov-report=html

# Expected coverage:
# ios_core: >75%
# api: >70%
# Overall: >72%

# All tests passing
# No critical or high priority bugs remaining

git commit -m "Week 5-6 complete: Optimization + Bug fixing"
git tag v0.1.0-week6