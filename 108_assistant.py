Пользователь хочет продолжить с production deployment guide. Создам следующие файлы:

1. Post-deployment validation procedures
2. Monitoring and alerting setup
3. Rollback procedures
4. Operations runbooks
5. Incident response for production

Продолжаю создавать файлы для production deployment.# 📦 PRODUCTION DEPLOYMENT GUIDE (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 3: `deployment/production/POST_DEPLOYMENT_VALIDATION.md`

```markdown
# Post-Deployment Validation

## 🎯 Overview

Comprehensive validation procedures to verify production deployment success.

**Validation Timeline:**
- T+0 to T+15min: Critical validation
- T+15min to T+1hr: Extended validation
- T+1hr to T+4hr: Monitoring period
- T+4hr to T+24hr: Stability verification

---

## ⚡ IMMEDIATE VALIDATION (T+0 to T+15min)

### 1. Service Health Checks

**API Health:**
```bash
# Test health endpoint
curl -f https://api.ios-system.com/health

# Expected response:
{
  "status": "healthy",
  "version": "v1.0.0",
  "timestamp": "2025-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy",
    "qdrant": "healthy"
  }
}
```

**Database Health:**
```bash
# Check database connectivity
kubectl exec -n ios-production deploy/ios-api -c api -- \
  python -c "from ios_core.database import test_connection; print(test_connection())"

# Expected: Connection successful

# Check database version
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "SELECT version();"

# Verify migration
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c \
  "SELECT version FROM alembic_version;"

# Expected: Latest migration version
```

**Redis Health:**
```bash
# Check Redis connectivity
kubectl exec -n ios-production deploy/redis -c redis -- redis-cli PING

# Expected: PONG

# Check Redis memory
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli INFO memory | grep used_memory_human

# Expected: <1GB for fresh deployment
```

**Search Services:**
```bash
# Elasticsearch health
curl -f https://elasticsearch.ios-system.com/_cluster/health

# Qdrant health
curl -f https://qdrant.ios-system.com/health
```

### 2. Critical Functionality Tests

**Authentication:**
```bash
# Test user login
curl -X POST https://api.ios-system.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "test_password"
  }'

# Expected: 200 OK with access_token

# Test token validation
curl -H "Authorization: Bearer $TOKEN" \
  https://api.ios-system.com/api/users/me

# Expected: 200 OK with user data
```

**Document Operations:**
```bash
# List documents
curl -H "Authorization: Bearer $TOKEN" \
  https://api.ios-system.com/api/documents?limit=10

# Expected: 200 OK with document list

# Create document
curl -X POST https://api.ios-system.com/api/documents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deployment Test Document",
    "content": "Testing document creation post-deployment"
  }'

# Expected: 201 Created with document data

# Get document
curl -H "Authorization: Bearer $TOKEN" \
  https://api.ios-system.com/api/documents/$DOC_ID

# Expected: 200 OK with document data

# Update document
curl -X PUT https://api.ios-system.com/api/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'

# Expected: 200 OK

# Delete document
curl -X DELETE https://api.ios-system.com/api/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN"

# Expected: 204 No Content
```

**Search Functionality:**
```bash
# Basic search
curl -H "Authorization: Bearer $TOKEN" \
  "https://api.ios-system.com/api/search?q=test&limit=10"

# Expected: 200 OK with search results

# Neural search
curl -X POST https://api.ios-system.com/api/search/neural \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "personal budget assistance",
    "limit": 10
  }'

# Expected: 200 OK with semantic results
```

### 3. Performance Validation

**Response Times:**
```bash
# Measure API response time
time curl -o /dev/null -s -w "%{time_total}\n" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.ios-system.com/api/documents

# Expected: <0.3s (300ms)

# Measure search response time
time curl -o /dev/null -s -w "%{time_total}\n" \
  -H "Authorization: Bearer $TOKEN" \
  "https://api.ios-system.com/api/search?q=test"

# Expected: <0.2s (200ms)
```

**Load Test (Light):**
```bash
# Run quick load test (50 concurrent users, 1 minute)
k6 run --vus 50 --duration 1m tests/load/k6-api-load-test.js

# Expected metrics:
# - Success rate: >99%
# - P95 response time: <500ms
# - Error rate: <1%
```

### 4. Security Validation

**SSL/TLS:**
```bash
# Check SSL certificate
echo | openssl s_client -connect api.ios-system.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# Verify:
# - Not expired
# - Valid for 90+ days

# Check SSL configuration
curl -I https://api.ios-system.com | grep -i "strict-transport-security"

# Expected: max-age=31536000
```

**WAF Rules:**
```bash
# Test SQL injection protection
curl "https://api.ios-system.com/api/search?q=test' OR '1'='1"

# Expected: 403 Forbidden (blocked by WAF)

# Test XSS protection
curl "https://api.ios-system.com/api/search?q=<script>alert('xss')</script>"

# Expected: 403 Forbidden (blocked by WAF)
```

**Rate Limiting:**
```bash
# Test rate limiting (send 150 requests rapidly)
for i in {1..150}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://api.ios-system.com/health &
done | grep 429 | wc -l

# Expected: At least 50 requests return 429 (rate limited)
```

---

## 🔍 EXTENDED VALIDATION (T+15min to T+1hr)

### 1. Integration Tests

**OAuth Integration:**
```bash
# Test Google OAuth
curl "https://api.ios-system.com/api/auth/oauth/google/authorize"

# Expected: 302 redirect to Google

# Test Microsoft OAuth
curl "https://api.ios-system.com/api/auth/oauth/microsoft/authorize"

# Expected: 302 redirect to Microsoft
```

**Email Integration:**
```bash
# Test password reset email
curl -X POST https://api.ios-system.com/api/auth/password-reset \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Expected: 200 OK

# Verify email sent (check logs)
kubectl logs -n ios-production deploy/ios-api -c api | grep "Password reset email sent"
```

**Webhook Integration:**
```bash
# Test webhook delivery
curl -X POST https://api.ios-system.com/api/webhooks/test \
  -H "Authorization: Bearer $TOKEN"

# Expected: 200 OK

# Verify webhook fired
# Check webhook endpoint logs
```

### 2. Data Integrity Checks

**Database:**
```bash
# Count records in key tables
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      'users' as table_name, COUNT(*) as count FROM users
    UNION ALL
    SELECT 'documents', COUNT(*) FROM documents
    UNION ALL
    SELECT 'domains', COUNT(*) FROM domains;
  "

# Verify counts match pre-deployment

# Check for orphaned records
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) FROM documents WHERE user_id NOT IN (SELECT id FROM users);
  "

# Expected: 0 (no orphaned documents)
```

**Search Indexes:**
```bash
# Verify Elasticsearch index count
curl https://elasticsearch.ios-system.com/_cat/indices?v | grep ios-documents

# Verify Qdrant collection
curl https://qdrant.ios-system.com/collections/documents
```

### 3. Monitoring Validation

**Prometheus Metrics:**
```bash
# Check metrics are being collected
curl https://prometheus.ios-system.com/api/v1/query?query=up | \
  jq '.data.result[] | select(.metric.job=="ios-api")'

# Expected: value = 1 (all instances up)

# Check request rate
curl 'https://prometheus.ios-system.com/api/v1/query?query=rate(http_requests_total[5m])' | \
  jq '.data.result[0].value[1]'

# Expected: >0 (requests flowing)
```

**Grafana Dashboards:**
```bash
# Test dashboard access
curl -u admin:$GRAFANA_PASSWORD \
  https://grafana.ios-system.com/api/dashboards/uid/ios-overview

# Expected: 200 OK with dashboard JSON
```

**Logs:**
```bash
# Verify logs flowing to ELK
curl -X POST https://elasticsearch.ios-system.com/logs-*/_search \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "range": {
        "@timestamp": {
          "gte": "now-5m"
        }
      }
    }
  }' | jq '.hits.total.value'

# Expected: >0 (recent logs present)
```

### 4. Cache Performance

**Redis Cache:**
```bash
# Check cache hit rate
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli INFO stats | grep keyspace_hits

# Calculate hit rate
# hits / (hits + misses) should be >80%

# Check cache size
kubectl exec -n ios-production deploy/redis -c redis -- \
  redis-cli DBSIZE

# Expected: >1000 keys (after warm-up)
```

**CDN Cache:**
```bash
# Check CDN hit rate (CloudFlare)
curl -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/analytics/dashboard" \
  -H "Authorization: Bearer $CF_TOKEN" | \
  jq '.result.timeseries[] | select(.since | contains("'$(date -u +%Y-%m-%d)'")) | .requests.cached'

# Expected: >90% cached requests
```

---

## 📊 MONITORING PERIOD (T+1hr to T+4hr)

### 1. Error Rate Monitoring

**Check Error Logs:**
```bash
# Monitor error rate
watch -n 60 'kubectl logs -n ios-production deploy/ios-api -c api --tail=100 | grep ERROR | wc -l'

# Expected: <10 errors per minute

# Check specific error types
kubectl logs -n ios-production deploy/ios-api -c api | \
  grep ERROR | \
  awk '{print $NF}' | \
  sort | uniq -c | sort -nr

# Investigate high-frequency errors
```

**Prometheus Alerts:**
```bash
# Check for firing alerts
curl https://prometheus.ios-system.com/api/v1/alerts | \
  jq '.data.alerts[] | select(.state=="firing")'

# Expected: Empty array (no firing alerts)

# Check alert history
curl https://alertmanager.ios-system.com/api/v2/alerts | \
  jq '.[] | {name: .labels.alertname, state: .status.state}'
```

### 2. Performance Monitoring

**Response Time Trends:**
```bash
# Query P50, P95, P99 latency
curl 'https://prometheus.ios-system.com/api/v1/query?query=histogram_quantile(0.95,rate(http_request_duration_seconds_bucket[5m]))' | \
  jq '.data.result[0].value[1]'

# Expected: <0.5 (500ms)

# Check slow queries
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT query, mean_exec_time, calls
    FROM pg_stat_statements
    WHERE mean_exec_time > 100
    ORDER BY mean_exec_time DESC
    LIMIT 10;
  "
```

**Resource Utilization:**
```bash
# Check CPU usage
kubectl top pods -n ios-production | grep ios-api

# Expected: <70% CPU

# Check memory usage
kubectl top pods -n ios-production | grep ios-api

# Expected: <80% memory

# Check disk usage
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  df -h /var/lib/postgresql/data

# Expected: <70% used
```

### 3. User Experience Monitoring

**Real User Monitoring (RUM):**
```bash
# Query frontend performance metrics
curl https://analytics.ios-system.com/api/rum/metrics | \
  jq '{
    page_load_time: .metrics.page_load_time,
    time_to_interactive: .metrics.tti,
    first_contentful_paint: .metrics.fcp
  }'

# Expected:
# - page_load_time: <3s
# - time_to_interactive: <5s
# - first_contentful_paint: <1.5s
```

**User Feedback:**
```bash
# Check support tickets created
curl -H "Authorization: Bearer $ZENDESK_TOKEN" \
  https://ios-system.zendesk.com/api/v2/tickets.json | \
  jq '[.tickets[] | select(.created_at > "'$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)'")]'

# Expected: <5 new tickets

# Check error reports
curl -H "Authorization: Bearer $SENTRY_TOKEN" \
  https://sentry.io/api/0/projects/ios-system/ios-api/events/ | \
  jq '[.[] | select(.dateCreated > "'$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)'")]'
```

---

## ✅ STABILITY VERIFICATION (T+4hr to T+24hr)

### 1. Extended Load Test

**Production Load Test:**
```bash
# Run extended load test (mirrors production traffic)
k6 run --vus 100 --duration 30m tests/load/k6-api-load-test.js

# Expected results:
# - Success rate: >99.5%
# - P95 response time: <500ms
# - P99 response time: <1000ms
# - Error rate: <0.5%
# - No memory leaks (memory stable)
```

### 2. Data Validation

**Data Consistency:**
```bash
# Verify data integrity
python scripts/validation/check_data_integrity.py

# Checks:
# - Foreign key constraints
# - Unique constraints
# - Data type consistency
# - Timestamp ordering

# Expected: All checks pass
```

**Backup Verification:**
```bash
# Verify automated backup ran
aws s3 ls s3://ios-system-backups/production/ | tail -1

# Expected: Backup from last hour

# Test restore (on staging)
./scripts/backup/restore.sh --environment staging --date $(date +%Y%m%d)

# Verify restore successful
```

### 3. Security Audit

**Security Scan:**
```bash
# Run automated security scan
python security/pentest/automated_security_scan.py \
  --target https://api.ios-system.com

# Expected: 0 critical, 0 high vulnerabilities

# Check WAF logs
kubectl logs -n ios-production deploy/modsecurity | \
  grep -i "attack" | tail -20

# Verify attacks blocked
```

**Access Audit:**
```bash
# Check unauthorized access attempts
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) FROM audit_logs
    WHERE action = 'failed_login'
    AND created_at > NOW() - INTERVAL '4 hours';
  "

# Expected: <100 failed attempts

# Check admin actions
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT user_id, action, COUNT(*)
    FROM audit_logs
    WHERE action LIKE 'admin_%'
    AND created_at > NOW() - INTERVAL '4 hours'
    GROUP BY user_id, action;
  "
```

---

## 📋 VALIDATION CHECKLIST

### Critical Validation (Must Pass)

- [ ] API health endpoint returns 200 OK
- [ ] Database connection successful
- [ ] Redis connection successful
- [ ] User authentication working
- [ ] Document CRUD operations working
- [ ] Search functionality working
- [ ] SSL/TLS certificate valid
- [ ] Error rate <1%
- [ ] P95 response time <500ms
- [ ] No critical alerts firing

### Extended Validation (Should Pass)

- [ ] OAuth integrations working
- [ ] Email sending working
- [ ] Webhooks delivering
- [ ] Monitoring collecting metrics
- [ ] Logs flowing to aggregator
- [ ] Cache hit rate >80%
- [ ] CDN serving static assets
- [ ] Backup completed successfully
- [ ] Security scan passed
- [ ] Load test passed

### 24-Hour Validation (Monitor)

- [ ] No memory leaks detected
- [ ] No performance degradation
- [ ] Error rate stable <0.5%
- [ ] User feedback positive
- [ ] Resource utilization stable
- [ ] No unexpected alerts
- [ ] Backup/restore tested
- [ ] Documentation updated

---

## 🚨 FAILURE CRITERIA

**Immediate Rollback Required:**
- Error rate >5% for 5 minutes
- Database connectivity lost
- P95 latency >2s for 5 minutes
- Critical security vulnerability
- Data corruption detected
- Service unavailable >5 minutes

**Investigation Required:**
- Error rate >1% but <5%
- P95 latency >500ms but <2s
- Cache hit rate <70%
- Memory leak suspected
- Unusual user feedback

---

## 📊 VALIDATION REPORT TEMPLATE

```markdown
# Deployment Validation Report

**Date:** 2025-01-15
**Version:** v1.0.0
**Deployment Duration:** 4h 23m

## Summary
- ✅ All critical validations passed
- ✅ All extended validations passed
- ⚠️ 2 minor issues identified (non-blocking)

## Critical Validation Results
| Check | Status | Notes |
|-------|--------|-------|
| API Health | ✅ Pass | Response time: 45ms |
| Database | ✅ Pass | All connections stable |
| Authentication | ✅ Pass | Login success rate: 99.8% |
| CRUD Operations | ✅ Pass | All operations working |
| Search | ✅ Pass | Latency p95: 120ms |

## Performance Metrics
- **Error Rate:** 0.3% (target: <1%) ✅
- **P95 Latency:** 180ms (target: <500ms) ✅
- **P99 Latency:** 320ms (target: <1s) ✅
- **Throughput:** 1,250 req/s (target: >1000) ✅
- **Cache Hit Rate:** 94% (target: >90%) ✅

## Issues Identified
1. **Minor:** CDN purge took 10 minutes (expected: 5 min)
   - Impact: Low
   - Resolution: Monitoring

2. **Minor:** 3 slow database queries (>200ms)
   - Impact: Low
   - Resolution: Added indexes, resolved

## Sign-off
- **DevOps:** [Name] ✅
- **Backend:** [Name] ✅
- **QA:** [Name] ✅
- **Security:** [Name] ✅

**Status:** ✅ DEPLOYMENT VALIDATED - PRODUCTION STABLE
```

---

**Next Steps:**
1. Continue monitoring for 24 hours
2. Schedule post-deployment review (within 48 hours)
3. Update runbooks with learnings
4. Plan next deployment improvements
```

---

## ФАЙЛ 4: `deployment/production/ROLLBACK_PROCEDURES.md`

```markdown
# Production Rollback Procedures

## 🔙 Overview

Emergency procedures for rolling back production deployment.

**Rollback Decision Criteria:**
- Error rate >5% for 5+ minutes
- P95 latency >2s for 5+ minutes
- Critical security vulnerability discovered
- Data corruption detected
- Service unavailable >5 minutes
- Database migration failed

---

## ⚡ EMERGENCY ROLLBACK (0-15 minutes)

### Step 1: Declare Rollback

**Announcement:**
```
🚨 PRODUCTION ROLLBACK IN PROGRESS 🚨

Incident: [Brief description]
Severity: Critical
Action: Rolling back to v0.9.9
ETA: 15 minutes

War Room: https://meet.google.com/xxx-xxxx-xxx
Status Channel: #incident-response

Incident Commander: [Name]
```

### Step 2: Stop New Traffic

```bash
# Enable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"true"}}'

# Or route traffic to maintenance page
kubectl patch ingress ios-ingress -n ios-production \
  --type=json \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "maintenance-page"}]'
```

### Step 3: Rollback Kubernetes Deployment

```bash
# Rollback to previous version
kubectl rollout undo deployment/ios-api -n ios-production
kubectl rollout undo deployment/ios-worker -n ios-production
kubectl rollout undo deployment/ios-scheduler -n ios-production

# Wait for rollout
kubectl rollout status deployment/ios-api -n ios-production --timeout=300s
kubectl rollout status deployment/ios-worker -n ios-production --timeout=300s

# Verify pods running
kubectl get pods -n ios-production | grep ios-api
```

### Step 4: Rollback Database (if needed)

**Check if database rollback needed:**
```bash
# Check current migration version
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "SELECT version FROM alembic_version;"

# If migration was applied in this deployment, rollback:
```

**Rollback database:**
```bash
# Method 1: Restore from backup (safest)
./scripts/backup/restore.sh \
  --backup backups/pre-deployment-20250115_100000/database.sql \
  --target production

# Method 2: Run rollback migration
kubectl exec -n ios-production deploy/ios-api -c api -- \
  python manage.py migrate <previous_migration_id>
```

**Verify database rollback:**
```bash
# Check migration version
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "SELECT version FROM alembic_version;"

# Run data integrity check
python scripts/validation/check_data_integrity.py
```

### Step 5: Clear Caches

```bash
# Clear Redis cache (stale data from new version)
kubectl exec -n ios-production deploy/redis -c redis -- redis-cli FLUSHDB

# Purge CDN cache
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/purge_cache" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -d '{"purge_everything":true}'
```

### Step 6: Restore Traffic

```bash
# Disable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"false"}}'

# Restore normal routing
kubectl patch ingress ios-ingress -n ios-production \
  --type=json \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value": "ios-api"}]'
```

### Step 7: Verify Rollback

```bash
# Check API health
curl https://api.ios-system.com/health

# Check version
curl https://api.ios-system.com/api/version

# Expected: Previous version (v0.9.9)

# Test critical functionality
./scripts/validation/smoke_tests.sh
```

---

## 🔍 DETAILED ROLLBACK PROCEDURES

### Rollback Scenario 1: Application Only

**When:** Code issues, no database changes

```bash
# Quick rollback (2-3 minutes)
kubectl rollout undo deployment/ios-api -n ios-production
kubectl rollout undo deployment/ios-worker -n ios-production

# Wait for completion
kubectl rollout status deployment/ios-api -n ios-production

# Clear application cache
kubectl exec -n ios-production deploy/redis -c redis -- redis-cli FLUSHDB

# Verify
curl https://api.ios-system.com/health
```

### Rollback Scenario 2: Database Migration Failed

**When:** Migration errors during deployment

```bash
# 1. Stop application (prevent partial migration)
kubectl scale deployment/ios-api --replicas=0 -n ios-production

# 2. Check migration status
kubectl logs -n ios-production job/db-migration-<timestamp> | tail -50

# 3. Restore database from pre-deployment backup
pg_restore -h $DB_HOST -U postgres -d ios_production \
  backups/pre-deployment-20250115_100000/database.sql

# 4. Verify restore
psql -h $DB_HOST -U postgres -d ios_production -c "
  SELECT COUNT(*) FROM users;
  SELECT COUNT(*) FROM documents;
"

# 5. Restore application to previous version
kubectl rollout undo deployment/ios-api -n ios-production
kubectl scale deployment/ios-api --replicas=3 -n ios-production

# 6. Verify
./scripts/validation/smoke_tests.sh
```

### Rollback Scenario 3: Data Corruption

**When:** Bad data written, database intact

```bash
# 1. Identify corrupt data
psql -h $DB_HOST -U postgres -d ios_production -c "
  SELECT * FROM documents
  WHERE updated_at > '2025-01-15 10:00:00'
  AND (title IS NULL OR content = '');
"

# 2. Stop writes
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"READ_ONLY_MODE":"true"}}'

# 3. Fix corrupt data
# Option A: Delete corrupt records
psql -h $DB_HOST -U postgres -d ios_production -c "
  DELETE FROM documents
  WHERE updated_at > '2025-01-15 10:00:00'
  AND (title IS NULL OR content = '');
"

# Option B: Restore from backup with timestamp
pg_restore --data-only \
  --table=documents \
  --data-only \
  backups/pre-deployment-20250115_100000/database.sql

# 4. Verify data integrity
python scripts/validation/check_data_integrity.py

# 5. Resume writes
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"READ_ONLY_MODE":"false"}}'
```

### Rollback Scenario 4: Complete System Failure

**When:** Multiple services down, need full restore

```bash
# 1. Declare emergency
# Send notifications to all stakeholders

# 2. Restore from complete backup
./scripts/disaster_recovery/full_restore.sh \
  --backup-date 2025-01-15 \
  --backup-time 10:00:00

# This script will:
# - Restore database from backup
# - Restore Redis from snapshot
# - Restore Vault snapshot
# - Deploy previous application version
# - Restore Kubernetes configs
# - Verify all services

# 3. Verify complete restoration
./scripts/validation/full_system_check.sh

# Expected: All services operational

# 4. Gradual traffic restoration
# Start with 10% traffic
# Increase to 50% after 15 minutes
# Full traffic after 30 minutes if stable
```

---

## 📋 ROLLBACK CHECKLIST

### Pre-Rollback

- [ ] Rollback decision approved by Incident Commander
- [ ] War room active (all stakeholders present)
- [ ] Backup verified available
- [ ] Maintenance notification sent to users
- [ ] Rollback script ready
- [ ] Team roles assigned

### During Rollback

- [ ] Maintenance mode enabled
- [ ] Application rolled back
- [ ] Database rolled back (if needed)
- [ ] Caches cleared
- [ ] Configuration restored
- [ ] Secrets verified
- [ ] Smoke tests passed

### Post-Rollback

- [ ] All services healthy
- [ ] Error rate normalized (<1%)
- [ ] Response time normalized (<500ms)
- [ ] Critical functionality verified
- [ ] Monitoring dashboards green
- [ ] No active alerts
- [ ] User notification sent (service restored)
- [ ] Incident report initiated

---

## 🚨 ROLLBACK AUTOMATION

### Automated Rollback Script

```bash
#!/bin/bash
# automated_rollback.sh
# Automatically rolls back deployment if criteria met

set -euo pipefail

NAMESPACE="ios-production"
ERROR_THRESHOLD=0.05  # 5%
LATENCY_THRESHOLD=2   # 2 seconds
CHECK_DURATION=300    # 5 minutes

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

check_error_rate() {
    local error_rate=$(kubectl exec -n monitoring deploy/prometheus -- \
        promtool query instant \
        'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])' \
        | grep -oP '\d+\.\d+' || echo "0")
    
    echo "$error_rate"
}

check_latency() {
    local p95_latency=$(kubectl exec -n monitoring deploy/prometheus -- \
        promtool query instant \
        'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))' \
        | grep -oP '\d+\.\d+' || echo "0")
    
    echo "$p95_latency"
}

trigger_rollback() {
    log "🚨 AUTOMATED ROLLBACK TRIGGERED"
    
    # Execute rollback
    ./scripts/rollback/emergency_rollback.sh
    
    # Send alerts
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d '{
            "text": "🚨 AUTOMATED ROLLBACK TRIGGERED",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Automated Rollback in Progress*\nReason: '"$1"'\nTime: '"$(date)"'"
                    }
                }
            ]
        }'
    
    # Page on-call
    curl -X POST "https://events.pagerduty.com/v2/enqueue" \
        -H "Content-Type: application/json" \
        -d '{
            "routing_key": "'"$PAGERDUTY_KEY"'",
            "event_action": "trigger",
            "payload": {
                "summary": "Automated Rollback Triggered: '"$1"'",
                "severity": "critical",
                "source": "ios-system-production"
            }
        }'
}

# Main monitoring loop
log "Starting automated rollback monitor..."

while true; do
    error_rate=$(check_error_rate)
    latency=$(check_latency)
    
    log "Error rate: $error_rate, Latency: ${latency}s"
    
    # Check error rate
    if (( $(echo "$error_rate > $ERROR_THRESHOLD" | bc -l) )); then
        trigger_rollback "Error rate exceeded: $error_rate (threshold: $ERROR_THRESHOLD)"
        break
    fi
    
    # Check latency
    if (( $(echo "$latency > $LATENCY_THRESHOLD" | bc -l) )); then
        trigger_rollback "Latency exceeded: ${latency}s (threshold: ${LATENCY_THRESHOLD}s)"
        break
    fi
    
    sleep 60
done
```

---

## 📊 ROLLBACK METRICS

### Track Rollback Performance

```bash
# Rollback duration
ROLLBACK_START=$(date +%s)
# ... perform rollback ...
ROLLBACK_END=$(date +%s)
ROLLBACK_DURATION=$((ROLLBACK_END - ROLLBACK_START))

echo "Rollback Duration: $ROLLBACK_DURATION seconds"

# Target: <15 minutes (900 seconds)

# Downtime during rollback
# Query Prometheus for availability
curl 'https://prometheus.ios-system.com/api/v1/query_range?query=up{job="ios-api"}&start='$ROLLBACK_START'&end='$ROLLBACK_END'&step=60' \
    | jq '.data.result[0].values | map(select(.[1] == "0")) | length'

# Calculate downtime percentage
```

### Post-Rollback Report

```markdown
# Rollback Report

**Date:** 2025-01-15 14:30:00 UTC
**Duration:** 12 minutes 34 seconds
**Reason:** Error rate exceeded 5% threshold

## Timeline
- 14:30:00 - Automated rollback triggered
- 14:32:15 - Application rolled back
- 14:35:00 - Database restored
- 14:38:45 - Caches cleared
- 14:40:00 - Traffic restored
- 14:42:34 - Rollback completed

## Impact
- **Users Affected:** ~500 (5% error rate)
- **Downtime:** 4 minutes 15 seconds
- **Requests Failed:** ~2,000

## Root Cause
[Brief description of what went wrong]

## Actions Taken
1. Automatic rollback triggered
2. Application reverted to v0.9.9
3. Database restored from backup
4. All caches cleared
5. Service restored

## Verification
- ✅ API health check passing
- ✅ Error rate normalized (0.2%)
- ✅ Response time normal (150ms p95)
- ✅ All smoke tests passing

## Next Steps
1. Root cause analysis scheduled
2. Fix developed and tested on staging
3. Re-deployment planned for tomorrow
4. Monitoring enhanced to detect issue earlier
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-15  
**Owner:** DevOps Team
```

---

**Продолжение следует...**

Создано:
- ✅ Post-deployment validation procedures (comprehensive)
- ✅ Rollback procedures (4 scenarios + automation)

**Следующие файлы:**
- Monitoring and alerting setup
- Operations runbooks
- Team onboarding guide

**Готовы продолжить?**