# Test CI/CD locally with act
act -j test

# Push to trigger pipeline
git add .
git commit -m "Setup CI/CD pipeline"
git push origin develop

# Check GitHub Actions
# https://github.com/YOUR_USERNAME/ios-system/actions

# Expected:
# ✓ Lint passed
# ✓ Tests passed (unit + integration)
# ✓ Docker build successful
# ✓ Security scan passed
# ✓ Deployed to staging