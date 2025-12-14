#!/bin/bash
# scripts/deploy.sh

set -e

echo "=========================================="
echo "IOS SEARCH - PRODUCTION DEPLOYMENT"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/ios"
BACKUP_DIR="/opt/ios/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Pre-deployment checks
log_info "Running pre-deployment checks..."

# Check if running as correct user
if [ "$USER" != "deploy" ]; then
    log_error "Must run as 'deploy' user"
    exit 1
fi

# Check if in project directory
cd $PROJECT_DIR

# Check if git repo is clean
if [[ -n $(git status -s) ]]; then
    log_warn "Working directory is not clean"
    git status -s
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Backup current state
log_info "Creating backup..."
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec -T postgres pg_dump -U ios_user ios_db > \
    $BACKUP_DIR/db_backup_$TIMESTAMP.sql
log_info "Database backed up to $BACKUP_DIR/db_backup_$TIMESTAMP.sql"

# Pull latest code
log_info "Pulling latest code..."
git pull origin main

# Build new images
log_info "Building Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Run database migrations
log_info "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm app \
    python manage.py migrate --noinput

# Collect static files
log_info "Collecting static files..."
docker-compose -f docker-compose.prod.yml run --rm app \
    python manage.py collectstatic --noinput

# Run tests
log_info "Running tests..."
docker-compose -f docker-compose.prod.yml run --rm app \
    pytest tests/smoke/ -v

if [ $? -ne 0 ]; then
    log_error "Tests failed! Aborting deployment."
    exit 1
fi

# Blue-Green Deployment Strategy
log_info "Starting blue-green deployment..."

# Scale up new instances
log_info "Scaling up new instances..."
docker-compose -f docker-compose.prod.yml up -d --scale app=4 --no-recreate

# Wait for new instances to be healthy
log_info "Waiting for new instances to be healthy..."
sleep 30

# Health check
for i in {1..5}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://ios-search.com/api/health/)
    if [ $HTTP_CODE -eq 200 ]; then
        log_info "Health check passed"
        break
    else
        log_warn "Health check failed (attempt $i/5): HTTP $HTTP_CODE"
        if [ $i -eq 5 ]; then
            log_error "Health checks failed. Rolling back..."
            docker-compose -f docker-compose.prod.yml up -d --scale app=2
            exit 1
        fi
        sleep 10
    fi
done

# Scale down old instances
log_info "Scaling down old instances..."
docker-compose -f docker-compose.prod.yml up -d --scale app=2

# Clean up old images
log_info "Cleaning up old Docker images..."
docker image prune -f

# Restart Nginx to reload configuration
log_info "Reloading Nginx..."
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload

# Warm cache
log_info "Warming cache..."
docker-compose -f docker-compose.prod.yml exec app \
    python manage.py warm_cache --popular-queries 100

# Final health check
log_info "Running final health check..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://ios-search.com/api/health/)
if [ $HTTP_CODE -eq 200 ]; then
    log_info "✓ Deployment successful!"
else
    log_error "✗ Final health check failed: HTTP $HTTP_CODE"
    exit 1
fi

# Send notification (optional)
# curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
#     -H 'Content-Type: application/json' \
#     -d '{"text":"🚀 IOS Search deployed successfully to production!"}'

echo "=========================================="
log_info "Deployment completed at $(date)"
echo "=========================================="

# Show deployment info
docker-compose -f docker-compose.prod.yml ps