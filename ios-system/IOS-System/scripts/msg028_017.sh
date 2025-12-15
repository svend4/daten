# Create release
git tag v0.1.0-alpha
git push --tags

# Package for PyPI
python -m build
twine upload --repository testpypi dist/*

# Announce
# - GitHub release notes
# - README update
# - Personal blog post