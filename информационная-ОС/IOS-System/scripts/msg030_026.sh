# All integration tests should pass
pytest tests/integration/ -v

# Check code quality
black --check .
mypy ios_core/
ruff check .

# Commit milestone
git add .
git commit -m "Week 1 complete: Core integration + first tests"
git tag v0.1.0-week1