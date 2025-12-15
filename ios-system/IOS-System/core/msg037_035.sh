# 1. Create release branch
git checkout -b release/v1.0.0

# 2. Update version
# - pyproject.toml
# - ios_core/__init__.py
# - package.json
# - docker-compose.yml

# 3. Update CHANGELOG.md
cat > CHANGELOG.md << 'EOF'
# Changelog

## [1.0.0] - 2025-01-15

### Added
- Automatic document classification
- Knowledge graph engine
- Multi-strategy search (full-text, semantic, hybrid)
- Context management
- REST API with JWT authentication
- WebSocket real-time updates
- Admin dashboard (React)
- Client SDKs (Python, JavaScript, Kotlin)
- Background task processing (Celery)
- Comprehensive documentation
- Docker & Kubernetes deployment
- CI/CD pipeline

### Security
- RBAC implementation
- Encryption at rest
- Input validation
- Rate limiting
- Security headers

### Performance
- Response time <300ms average
- Throughput >150 req/s
- Database optimization
- Redis caching
- Connection pooling

[1.0.0]: https://github.com/ios-system/ios-system/releases/tag/v1.0.0
EOF

# 4. Commit and tag
git add .
git commit -m "Release v1.0.0"
git tag -a v1.0.0 -m "Release version 1.0.0"

# 5. Merge to main
git checkout main
git merge release/v1.0.0

# 6. Push
git push origin main
git push origin v1.0.0

# 7. Create GitHub release
gh release create v1.0.0 \
  --title "IOS System v1.0.0" \
  --notes-file ANNOUNCEMENT.md \
  --discussion-category "Announcements"

# 8. Publish Docker images
docker push ghcr.io/your-org/ios-system:1.0.0
docker push ghcr.io/your-org/ios-system:latest

# 9. Publish to PyPI (if applicable)
python -m build
twine upload dist/*