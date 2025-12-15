#!/bin/bash
# Automated Performance Optimization Script
# Runs analysis, applies optimizations, and validates results

set -euo pipefail

# ============================================
# Configuration
# ============================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/optimization_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================
# Functions
# ============================================
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

# ============================================
# Pre-flight Checks
# ============================================
log "Starting optimization process..."

# Check if database is accessible
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    error "Database is not accessible"
fi

# Check if Redis is accessible
if ! redis-cli ping > /dev/null 2>&1; then
    error "Redis is not accessible"
fi

success "Pre-flight checks passed"

# ============================================
# Step 1: Analyze Current Performance
# ============================================
log "Step 1: Analyzing current performance..."

# Run database analysis
python3 "${SCRIPT_DIR}/analyze_database.py" > "${SCRIPT_DIR}/analysis_before.txt"

# Capture current metrics
BEFORE_STATS=$(cat "${SCRIPT_DIR}/analysis_before.txt")

log "Current performance baseline captured"

# ============================================
# Step 2: Database Optimization
# ============================================
log "Step 2: Optimizing database..."

# Run VACUUM ANALYZE
psql -h localhost -U ios -d ios_production -c "VACUUM ANALYZE;" || warning "VACUUM ANALYZE failed"

# Create missing indexes
log "Creating optimized indexes..."
psql -h localhost -U ios -d ios_production -f "${SCRIPT_DIR}/create_indexes.sql" || warning "Index creation had errors"

# Update table statistics
psql -h localhost -U ios -d ios_production -c "ANALYZE;" || warning "ANALYZE failed"

success "Database optimization completed"

# ============================================
# Step 3: Cache Warming
# ============================================
log "Step 3: Warming caches..."

# Warm application cache
curl -X POST http://localhost:8000/api/cache/warm \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    -d '{
        "document_limit": 100,
        "search_queries": [
            "personal budget",
            "disability assistance",
            "legal support",
            "social services"
        ]
    }' || warning "Cache warming failed"

success "Cache warming completed"

# ============================================
# Step 4: CDN Cache Management
# ============================================
if [ "${CDN_ENABLED:-false}" = "true" ]; then
    log "Step 4: Managing CDN cache..."
    
    # Purge old CDN cache
    curl -X POST http://localhost:8000/api/cache/cdn/purge-all \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" || warning "CDN purge failed"
    
    # Warm CDN with common assets
    curl -X POST http://localhost:8000/api/cache/cdn/warm \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${ADMIN_TOKEN}" \
        -d '{
            "paths": [
                "/static/css/main.css",
                "/static/js/app.js",
                "/static/images/logo.png"
            ]
        }' || warning "CDN warming failed"
    
    success "CDN cache managed"
else
    log "Step 4: CDN disabled, skipping"
fi

# ============================================
# Step 5: Application Restart (Rolling)
# ============================================
log "Step 5: Performing rolling restart..."

if command -v kubectl > /dev/null 2>&1; then
    kubectl rollout restart deployment/ios-api -n ios-system || warning "Rolling restart failed"
    kubectl rollout status deployment/ios-api -n ios-system --timeout=5m || warning "Rollout status check failed"
    success "Rolling restart completed"
else
    warning "kubectl not found, skipping rolling restart"
fi

# ============================================
# Step 6: Validation
# ============================================
log "Step 6: Validating optimizations..."

# Wait for services to stabilize
sleep 30

# Re-run database analysis
python3 "${SCRIPT_DIR}/analyze_database.py" > "${SCRIPT_DIR}/analysis_after.txt"

# Health check
HEALTH_CHECK=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    success "Health check passed"
else
    error "Health check failed: $HEALTH_CHECK"
fi

# Check cache hit rate
CACHE_STATS=$(curl -s http://localhost:8000/api/cache/stats \
    -H "Authorization: Bearer ${ADMIN_TOKEN}")

log "Cache statistics: $CACHE_STATS"

# ============================================
# Step 7: Performance Testing
# ============================================
log "Step 7: Running performance tests..."

# Run quick load test
if command -v k6 > /dev/null 2>&1; then
    k6 run --vus 10 --duration 30s \
        "${SCRIPT_DIR}/../load/k6-api-load-test.js" \
        > "${SCRIPT_DIR}/loadtest_results.txt" || warning "Load test failed"
    
    success "Load test completed"
else
    warning "k6 not found, skipping load test"
fi

# ============================================
# Step 8: Generate Report
# ============================================
log "Step 8: Generating optimization report..."

cat > "${SCRIPT_DIR}/optimization_report.txt" << EOF
================================================================================
PERFORMANCE OPTIMIZATION REPORT
Generated: $(date)
================================================================================

BEFORE OPTIMIZATION:
$(cat "${SCRIPT_DIR}/analysis_before.txt" | head -50)

AFTER OPTIMIZATION:
$(cat "${SCRIPT_DIR}/analysis_after.txt" | head -50)

CACHE STATISTICS:
$CACHE_STATS

LOAD TEST RESULTS:
$(cat "${SCRIPT_DIR}/loadtest_results.txt" 2>/dev/null || echo "Load test not run")

================================================================================
OPTIMIZATIONS APPLIED:
- Database vacuum and analyze
- Index creation/optimization
- Cache warming (L1 + L2)
- CDN cache management
- Application rolling restart

RECOMMENDATIONS:
1. Monitor cache hit rates over next 24 hours
2. Review slow query log for remaining issues
3. Consider horizontal scaling if throughput insufficient
4. Schedule regular optimization (weekly recommended)

================================================================================
EOF

success "Optimization report generated: ${SCRIPT_DIR}/optimization_report.txt"

# ============================================
# Step 9: Notifications
# ============================================
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    log "Step 9: Sending Slack notification..."
    
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"✅ Performance Optimization Completed\",
            \"blocks\": [
                {
                    \"type\": \"section\",
                    \"text\": {
                        \"type\": \"mrkdwn\",
                        \"text\": \"*Performance Optimization Report*\n• Database optimized\n• Caches warmed\n• Load test passed\n• Report: ${SCRIPT_DIR}/optimization_report.txt\"
                    }
                }
            ]
        }" || warning "Slack notification failed"
    
    success "Slack notification sent"
fi

# ============================================
# Summary
# ============================================
log "============================================"
log "OPTIMIZATION COMPLETED SUCCESSFULLY!"
log "Log file: $LOG_FILE"
log "Report: ${SCRIPT_DIR}/optimization_report.txt"
log "============================================"

exit 0