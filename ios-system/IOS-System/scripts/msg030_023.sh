# Verify setup
python -c "from ios_core.system import IOSSystem; print('✓ Import successful')"
pytest --collect-only  # Should show 0 tests (we'll add them next)
black --check ios_core/
mypy ios_core/