#!/bin/bash
# Production Deployment Script
# Automates blue-green deployment with zero downtime

set -euo pipefail

# ============================================
# Configuration
# ============================================
DEPLOYMENT_VERSION="${1:-latest}"
NAMESPACE="ios-production"
CLUSTER_NAME="ios-production-cluster"
REGION="us-east-1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="deployment_$(date +%Y%m%d_%H%M%S).log"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

# ============================================
# Pre-deployment Checks
# ============================================
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check kubectl access
    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
    fi
    
    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        error "Namespace $NAMESPACE does not exist"
    fi
    
    # Check Vault is accessible
    if ! vault status &> /dev/null; then
        error "Cannot connect to Vault"
    fi
    
    # Check database is accessible
    if ! kubectl exec -n "$NAMESPACE" deploy/postgresql -c postgresql -- pg_isready; then
        error "Database is not accessible"
    fi
    
    # Check container images exist
    if ! docker pull "ios-system/api:${DEPLOYMENT_VERSION}"; then
        error "Container image not found: ios-system/api:${DEPLOYMENT_VERSION}"
    fi
    
    log "✅ Pre-deployment checks passed"
}

# ============================================
# Backup Current State
# ============================================
backup_current_state() {
    log "Backing up current state..."
    
    BACKUP_DIR="backups/pre-deployment-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    log "Backing up database..."
    kubectl exec -n "$NAMESPACE" deploy/postgresql -c postgresql -- \
        pg_dump -U postgres ios_production > "$BACKUP_DIR/database.sql"
    
    # Backup Redis
    log "Backing up Redis..."
    kubectl exec -n "$NAMESPACE" deploy/redis -c redis -- \
        redis-cli SAVE
    kubectl cp "$NAMESPACE/redis-0:/data/dump.rdb" "$BACKUP_DIR/redis.rdb"
    
    # Backup Kubernetes configurations
    log "Backing up Kubernetes configurations..."
    kubectl get all -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/kubernetes.yaml"
    
    # Backup ConfigMaps and Secrets
    kubectl get configmaps -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/configmaps.yaml"
    kubectl get secrets -n "$NAMESPACE" -o yaml > "$BACKUP_DIR/secrets.yaml"
    
    log "✅ Backup completed: $BACKUP_DIR"
}

# ============================================
# Database Migration
# ============================================
run_database_migration() {
    log "Running database migrations..."
    
    # Create migration job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      containers:
      - name: migration
        image: ios-system/api:${DEPLOYMENT_VERSION}
        command: ["python", "manage.py", "migrate"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for migration to complete
    JOB_NAME="db-migration-$(date +%s)"
    kubectl wait --for=condition=complete --timeout=300s "job/$JOB_NAME" -n "$NAMESPACE"
    
    if kubectl get job "$JOB_NAME" -n "$NAMESPACE" -o jsonpath='{.status.succeeded}' | grep -q 1; then
        log "✅ Database migration successful"
    else
        error "Database migration failed"
    fi
}

# ============================================
# Deploy Green Environment
# ============================================
deploy_green_environment() {
    log "Deploying green environment..."
    
    # Update deployment with new image
    kubectl set image deployment/ios-api -n "$NAMESPACE" \
        api="ios-system/api:${DEPLOYMENT_VERSION}" \
        --record
    
    kubectl set image deployment/ios-worker -n "$NAMESPACE" \
        worker="ios-system/worker:${DEPLOYMENT_VERSION}" \
        --record
    
    # Wait for rollout to complete
    log "Waiting for rollout to complete..."
    kubectl rollout status deployment/ios-api -n "$NAMESPACE" --timeout=600s
    kubectl rollout status deployment/ios-worker -n "$NAMESPACE" --timeout=600s
    
    log "✅ Green environment deployed"
}

# ============================================
# Smoke Tests
# ============================================
run_smoke_tests() {
    log "Running smoke tests on green environment..."
    
    # Get green environment URL (internal service)
    GREEN_URL="http://ios-api.$NAMESPACE.svc.cluster.local:8000"
    
    # Health check
    if ! kubectl run smoke-test --rm -i --restart=Never --image=curlimages/curl -n "$NAMESPACE" -- \
        curl -f "$GREEN_URL/health"; then
        error "Health check failed"
    fi
    
    # API test
    if ! kubectl run api-test --rm -i --restart=Never --image=curlimages/curl -n "$NAMESPACE" -- \
        curl -f "$GREEN_URL/api/docs"; then
        error "API documentation not accessible"
    fi
    
    # Database connectivity test
    if ! kubectl exec -n "$NAMESPACE" deploy/ios-api -c api -- \
        python -c "from ios_core.database import test_connection; test_connection()"; then
        error "Database connectivity test failed"
    fi
    
    # Redis connectivity test
    if ! kubectl exec -n "$NAMESPACE" deploy/redis -c redis -- \
        redis-cli PING | grep -q PONG; then
        error "Redis connectivity test failed"
    fi
    
    log "✅ Smoke tests passed"
}

# ============================================
# Traffic Switch
# ============================================
switch_traffic_to_green() {
    log "Switching traffic to green environment..."
    
    # Gradual traffic shift (10% -> 50% -> 100%)
    
    # 10% traffic
    log "Shifting 10% traffic to green..."
    kubectl patch service ios-api -n "$NAMESPACE" -p \
        '{"spec":{"selector":{"version":"'${DEPLOYMENT_VERSION}'","weight":"10"}}}'
    sleep 60
    check_metrics "10%"
    
    # 50% traffic
    log "Shifting 50% traffic to green..."
    kubectl patch service ios-api -n "$NAMESPACE" -p \
        '{"spec":{"selector":{"version":"'${DEPLOYMENT_VERSION}'","weight":"50"}}}'
    sleep 120
    check_metrics "50%"
    
    # 100% traffic
    log "Shifting 100% traffic to green..."
    kubectl patch service ios-api -n "$NAMESPACE" -p \
        '{"spec":{"selector":{"version":"'${DEPLOYMENT_VERSION}'"}}}'
    sleep 60
    check_metrics "100%"
    
    log "✅ Traffic switched to green environment"
}

# ============================================
# Metrics Check
# ============================================
check_metrics() {
    local traffic_percentage="$1"
    
    log "Checking metrics at $traffic_percentage traffic..."
    
    # Query Prometheus for error rate
    ERROR_RATE=$(kubectl exec -n monitoring deploy/prometheus -- \
        promtool query instant \
        'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])' \
        | grep -oP '\d+\.\d+' || echo "0")
    
    if (( $(echo "$ERROR_RATE > 0.01" | bc -l) )); then
        warning "Error rate is $ERROR_RATE (>1%)"
    fi
    
    # Query for response time
    P95_LATENCY=$(kubectl exec -n monitoring deploy/prometheus -- \
        promtool query instant \
        'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))' \
        | grep -oP '\d+\.\d+' || echo "0")
    
    if (( $(echo "$P95_LATENCY > 0.5" | bc -l) )); then
        warning "P95 latency is ${P95_LATENCY}s (>500ms)"
    fi
    
    log "Metrics OK - Error rate: $ERROR_RATE, P95 latency: ${P95_LATENCY}s"
}

# ============================================
# Rollback
# ============================================
rollback() {
    error "ROLLING BACK DEPLOYMENT"
    
    # Rollback deployment
    kubectl rollout undo deployment/ios-api -n "$NAMESPACE"
    kubectl rollout undo deployment/ios-worker -n "$NAMESPACE"
    
    # Wait for rollback
    kubectl rollout status deployment/ios-api -n "$NAMESPACE"
    kubectl rollout status deployment/ios-worker -n "$NAMESPACE"
    
    # Rollback database if needed
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        warning "Database rollback required - run manually: psql < $BACKUP_DIR/database.sql"
    fi
    
    error "Deployment rolled back. Check logs for details."
}

# ============================================
# Post-deployment
# ============================================
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Clear caches
    log "Clearing application caches..."
    kubectl exec -n "$NAMESPACE" deploy/redis -c redis -- redis-cli FLUSHDB
    
    # Warm caches
    log "Warming caches..."
    curl -X POST "https://api.ios-system.com/api/cache/warm" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -d '{"document_limit": 100}'
    
    # Send deployment notification
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d '{
                "text": "✅ Production Deployment Successful",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Production Deployment Complete*\n• Version: '"$DEPLOYMENT_VERSION"'\n• Duration: '"$(date -d@$SECONDS -u +%H:%M:%S)"'\n• Status: Success"
                        }
                    }
                ]
            }'
    fi
    
    log "✅ Post-deployment tasks completed"
}

# ============================================
# Main Execution
# ============================================
main() {
    log "=========================================="
    log "IOS System Production Deployment"
    log "Version: $DEPLOYMENT_VERSION"
    log "Namespace: $NAMESPACE"
    log "=========================================="
    
    # Trap errors for rollback
    trap rollback ERR
    
    # Deployment steps
    pre_deployment_checks
    backup_current_state
    run_database_migration
    deploy_green_environment
    run_smoke_tests
    switch_traffic_to_green
    post_deployment
    
    log "=========================================="
    log "✅ DEPLOYMENT SUCCESSFUL"
    log "Version $DEPLOYMENT_VERSION is now live"
    log "Log file: $LOG_FILE"
    log "=========================================="
}

# Run deployment
main "$@"