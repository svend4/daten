Пользователь хочет продолжить. Создам оставшиеся 5 runbooks:
- Deployment Rollback
- Database Backup & Restore
- Certificate Renewal
- Scaling Operations
- Security Incident

Продолжу в том же формате - подробные пошаговые инструкции с командами.# 📦 PRODUCTION DEPLOYMENT GUIDE (ПРОДОЛЖЕНИЕ)

## RUNBOOK 6: Deployment Rollback

### Symptoms
- Recent deployment causing issues
- Error rate spike after deployment
- Performance degradation post-deployment
- Failed deployment

### Impact
- **Severity:** Critical (if deployment breaks production)
- **User Impact:** Varies based on issue
- **Business Impact:** Service disruption

### Investigation Steps

**Step 1: Verify Deployment Timeline**
```bash
# Check recent deployments
kubectl rollout history deployment/ios-api -n ios-production

# Get deployment details
kubectl describe deployment/ios-api -n ios-production | grep -A 5 "Events"

# Check when metrics started degrading
curl 'https://prometheus.ios-system.com/api/v1/query_range?query=api:http_errors:rate5m&start='$(date -d '2 hours ago' +%s)'&end='$(date +%s)'&step=60' | \
  jq '.data.result[0].values[] | select(.[1] | tonumber > 0.01)'
```

**Step 2: Compare Versions**
```bash
# Current version
kubectl get deployment/ios-api -n ios-production -o json | \
  jq '.spec.template.spec.containers[0].image'

# Previous version
kubectl rollout history deployment/ios-api -n ios-production --revision=1

# Check what changed
git diff v1.0.0 v1.1.0 --stat
```

**Step 3: Check Rollback Impact**
```bash
# Check if database migration was applied
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "SELECT version FROM alembic_version;"

# Check if new data written that depends on new schema
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) FROM information_schema.columns
    WHERE table_name = 'documents'
    AND column_name NOT IN (
      SELECT column_name FROM information_schema.columns
      WHERE table_schema = 'public_v1_0_0'
    );
  "
```

### Resolution Procedures

**Quick Rollback (Application Only)**
```bash
# 1. Announce rollback
# Post to #incidents channel

# 2. Rollback deployment
kubectl rollout undo deployment/ios-api -n ios-production
kubectl rollout undo deployment/ios-worker -n ios-production

# 3. Wait for rollout
kubectl rollout status deployment/ios-api -n ios-production --timeout=300s

# 4. Verify health
curl https://api.ios-system.com/health

# 5. Check error rate
watch -n 10 'curl -s "https://prometheus.ios-system.com/api/v1/query?query=api:http_errors:rate5m"'

# 6. Clear application cache
kubectl exec -n ios-production deploy/redis -c redis -- redis-cli FLUSHDB

# 7. Announce rollback complete
```

**Full Rollback (Application + Database)**
```bash
# ⚠️ CRITICAL: This involves database restore - coordinate with team

# 1. Enable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"true"}}'

# 2. Stop application
kubectl scale deployment/ios-api --replicas=0 -n ios-production
kubectl scale deployment/ios-worker --replicas=0 -n ios-production

# 3. Restore database from pre-deployment backup
BACKUP_FILE="backups/pre-deployment-$(date +%Y%m%d)/database.sql"

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'ios_production' AND pid <> pg_backend_pid();
  "

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "DROP DATABASE ios_production;"

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "CREATE DATABASE ios_production;"

kubectl cp "$BACKUP_FILE" ios-production/postgresql-0:/tmp/restore.sql

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -f /tmp/restore.sql

# 4. Verify database restore
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) FROM users;
    SELECT COUNT(*) FROM documents;
    SELECT version FROM alembic_version;
  "

# 5. Rollback application
kubectl set image deployment/ios-api -n ios-production \
  api=ios-system/api:v1.0.0

kubectl scale deployment/ios-api --replicas=3 -n ios-production
kubectl scale deployment/ios-worker --replicas=2 -n ios-production

# 6. Wait for rollout
kubectl rollout status deployment/ios-api -n ios-production

# 7. Run smoke tests
./scripts/validation/smoke_tests.sh

# 8. Disable maintenance mode
kubectl patch configmap ios-config -n ios-production \
  -p '{"data":{"MAINTENANCE_MODE":"false"}}'

# 9. Monitor for 30 minutes
watch -n 30 './scripts/monitoring/check_health.sh'
```

**Partial Rollback (Feature Flags)**
```bash
# If new feature causing issues, disable via feature flag

# 1. Disable problematic feature
kubectl set env deployment/ios-api -n ios-production \
  FEATURE_NEW_SEARCH_ENABLED=false

# 2. Restart pods to pick up change
kubectl rollout restart deployment/ios-api -n ios-production

# 3. Verify feature disabled
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  https://api.ios-system.com/api/admin/features

# 4. Monitor error rate
watch -n 10 'curl -s "https://prometheus.ios-system.com/api/v1/query?query=api:http_errors:rate5m"'

# This allows keeping new deployment while disabling broken feature
```

### Post-Rollback

**Step 1: Document Incident**
```markdown
# Rollback Incident Report

**Date:** 2025-01-15 14:30 UTC
**Duration:** 45 minutes
**Rollback Type:** Full (Application + Database)

## Timeline
- 14:00 - Deployment v1.1.0 completed
- 14:15 - Error rate increased to 8%
- 14:20 - Decision to rollback
- 14:25 - Maintenance mode enabled
- 14:30 - Database restored
- 14:40 - Application rolled back
- 14:45 - Service restored

## Root Cause
[Brief description]

## Impact
- Users affected: ~1,500
- Data loss: None (restored from backup)
- Revenue impact: ~€500 (estimated)

## Actions
1. Rollback completed successfully
2. Bug identified and assigned
3. Fix scheduled for tomorrow
```

**Step 2: Review & Learn**
```bash
# Schedule post-mortem within 24 hours
# Invite: Engineering, DevOps, Product, QA

# Topics to cover:
# - What went wrong?
# - Why didn't we catch it in testing?
# - How can we prevent this?
# - What can we improve in rollback process?
```

### Prevention
- [ ] Implement canary deployments
- [ ] Increase test coverage
- [ ] Add more staging environment testing
- [ ] Implement feature flags for all new features
- [ ] Automated rollback triggers
- [ ] Blue-green deployment strategy

### Escalation
- **Decision to rollback:** Engineering Lead approval
- **Database rollback:** CTO approval required
- **Communication:** Notify all stakeholders immediately

---

## RUNBOOK 7: Database Backup & Restore

### Backup Procedures

**Automated Daily Backup**
```bash
# Backup script runs daily via CronJob
# Location: kubernetes/cronjobs/backup.yaml

apiVersion: batch/v1
kind: CronJob
metadata:
  name: database-backup
  namespace: ios-production
spec:
  schedule: "0 2 * * *"  # 2 AM UTC daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:14
            command:
            - /bin/bash
            - -c
            - |
              BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
              BACKUP_FILE="ios_production_${BACKUP_DATE}.sql"
              
              pg_dump -h postgresql -U postgres ios_production > /tmp/${BACKUP_FILE}
              
              gzip /tmp/${BACKUP_FILE}
              
              aws s3 cp /tmp/${BACKUP_FILE}.gz s3://ios-system-backups/production/${BACKUP_FILE}.gz
              
              # Keep only 30 days of backups
              aws s3 ls s3://ios-system-backups/production/ | \
                awk '{print $4}' | \
                sort -r | \
                tail -n +31 | \
                xargs -I {} aws s3 rm s3://ios-system-backups/production/{}
          restartPolicy: OnFailure
```

**Manual Backup**
```bash
# Create immediate backup

# 1. Set backup filename
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="ios_production_manual_${BACKUP_DATE}.sql"

# 2. Create backup
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  pg_dump -U postgres -Fc ios_production > "${BACKUP_FILE}"

# 3. Compress backup
gzip "${BACKUP_FILE}"

# 4. Upload to S3
aws s3 cp "${BACKUP_FILE}.gz" \
  s3://ios-system-backups/production/manual/

# 5. Verify backup
aws s3 ls s3://ios-system-backups/production/manual/ | grep "${BACKUP_FILE}"

# 6. Test restore on staging (recommended)
./scripts/backup/test_restore.sh --backup "${BACKUP_FILE}.gz" --env staging
```

**Point-in-Time Recovery (PITR) Setup**
```bash
# Configure WAL archiving for PITR

# 1. Update PostgreSQL config
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "
    ALTER SYSTEM SET wal_level = replica;
    ALTER SYSTEM SET archive_mode = on;
    ALTER SYSTEM SET archive_command = 'aws s3 cp %p s3://ios-system-wal-archive/%f';
    ALTER SYSTEM SET archive_timeout = 300;
  "

# 2. Restart PostgreSQL
kubectl rollout restart statefulset/postgresql -n ios-production

# 3. Verify WAL archiving
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "SHOW archive_mode;"

# 4. Check archived WALs
aws s3 ls s3://ios-system-wal-archive/ | tail -10
```

### Restore Procedures

**Full Database Restore**
```bash
# ⚠️ CRITICAL: This will overwrite production database

# 1. List available backups
aws s3 ls s3://ios-system-backups/production/ | sort -r | head -10

# 2. Download backup
BACKUP_FILE="ios_production_20250115_020000.sql.gz"
aws s3 cp "s3://ios-system-backups/production/${BACKUP_FILE}" .

# 3. Decompress
gunzip "${BACKUP_FILE}"

# 4. Stop application (prevent writes)
kubectl scale deployment/ios-api --replicas=0 -n ios-production
kubectl scale deployment/ios-worker --replicas=0 -n ios-production

# 5. Terminate existing connections
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = 'ios_production' AND pid <> pg_backend_pid();
  "

# 6. Drop and recreate database
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "DROP DATABASE ios_production;"

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "CREATE DATABASE ios_production;"

# 7. Restore backup
kubectl cp "${BACKUP_FILE%.gz}" \
  ios-production/postgresql-0:/tmp/restore.sql

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  pg_restore -U postgres -d ios_production -v /tmp/restore.sql

# 8. Verify restore
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT 
      'users' as table_name, COUNT(*) as count FROM users
    UNION ALL
    SELECT 'documents', COUNT(*) FROM documents
    UNION ALL
    SELECT 'domains', COUNT(*) FROM domains;
  "

# 9. Restart application
kubectl scale deployment/ios-api --replicas=3 -n ios-production
kubectl scale deployment/ios-worker --replicas=2 -n ios-production

# 10. Run smoke tests
./scripts/validation/smoke_tests.sh

# 11. Monitor for issues
watch -n 30 './scripts/monitoring/check_health.sh'
```

**Point-in-Time Restore**
```bash
# Restore database to specific timestamp

# 1. Stop application
kubectl scale deployment/ios-api --replicas=0 -n ios-production

# 2. Find base backup before target time
TARGET_TIME="2025-01-15 14:30:00"
BASE_BACKUP="ios_production_20250115_020000.sql.gz"

# 3. Download and restore base backup
aws s3 cp "s3://ios-system-backups/production/${BASE_BACKUP}" .
gunzip "${BASE_BACKUP}"

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "DROP DATABASE ios_production;"
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -c "CREATE DATABASE ios_production;"

kubectl cp "${BASE_BACKUP%.gz}" ios-production/postgresql-0:/tmp/restore.sql
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  pg_restore -U postgres -d ios_production /tmp/restore.sql

# 4. Download WAL files
mkdir -p wal_restore
aws s3 sync s3://ios-system-wal-archive/ ./wal_restore/

# 5. Configure recovery
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  bash -c "cat > /var/lib/postgresql/data/recovery.conf <<EOF
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '${TARGET_TIME}'
recovery_target_action = 'promote'
EOF"

# 6. Copy WAL files
kubectl cp ./wal_restore/ ios-production/postgresql-0:/wal_archive/

# 7. Restart PostgreSQL
kubectl rollout restart statefulset/postgresql -n ios-production

# 8. Monitor recovery
kubectl logs -f statefulset/postgresql -n ios-production | grep recovery

# 9. Verify target time reached
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT pg_last_xact_replay_timestamp();
  "

# 10. Restart application
kubectl scale deployment/ios-api --replicas=3 -n ios-production
```

**Table-Level Restore**
```bash
# Restore single table without full database restore

# 1. Download backup
BACKUP_FILE="ios_production_20250115_020000.sql.gz"
aws s3 cp "s3://ios-system-backups/production/${BACKUP_FILE}" .
gunzip "${BACKUP_FILE}"

# 2. Extract single table
pg_restore -t documents "${BACKUP_FILE%.gz}" > documents_restore.sql

# 3. Restore to temporary table
kubectl cp documents_restore.sql ios-production/postgresql-0:/tmp/

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    CREATE TABLE documents_restore AS TABLE documents WITH NO DATA;
  "

kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -f /tmp/documents_restore.sql

# 4. Compare data
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    SELECT COUNT(*) as current FROM documents;
    SELECT COUNT(*) as restored FROM documents_restore;
  "

# 5. Swap tables (if needed)
# ⚠️ CAREFUL: This will replace current data
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "
    BEGIN;
    ALTER TABLE documents RENAME TO documents_old;
    ALTER TABLE documents_restore RENAME TO documents;
    COMMIT;
  "

# 6. Drop old table after verification
kubectl exec -n ios-production deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_production -c "DROP TABLE documents_old;"
```

### Backup Verification

**Test Restore (Staging)**
```bash
# Regularly test restores on staging environment

# 1. Get latest production backup
LATEST_BACKUP=$(aws s3 ls s3://ios-system-backups/production/ | \
  sort -r | head -1 | awk '{print $4}')

# 2. Download backup
aws s3 cp "s3://ios-system-backups/production/${LATEST_BACKUP}" .

# 3. Restore to staging
kubectl exec -n ios-staging deploy/postgresql -c postgresql -- \
  psql -U postgres -c "DROP DATABASE IF EXISTS ios_staging;"

kubectl exec -n ios-staging deploy/postgresql -c postgresql -- \
  psql -U postgres -c "CREATE DATABASE ios_staging;"

kubectl cp "${LATEST_BACKUP%.gz}" ios-staging/postgresql-0:/tmp/restore.sql

kubectl exec -n ios-staging deploy/postgresql -c postgresql -- \
  pg_restore -U postgres -d ios_staging /tmp/restore.sql

# 4. Run validation queries
kubectl exec -n ios-staging deploy/postgresql -c postgresql -- \
  psql -U postgres -d ios_staging -c "
    SELECT tablename, n_live_tup
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC;
  "

# 5. Test application on staging
curl https://api.staging.ios-system.com/health

# 6. Document test results
echo "Backup test successful: ${LATEST_BACKUP}" >> backup_test_log.txt
```

**Backup Monitoring**
```bash
# Monitor backup success/failure

# 1. Check last backup time
LAST_BACKUP=$(aws s3 ls s3://ios-system-backups/production/ | \
  sort -r | head -1 | awk '{print $1, $2}')

echo "Last backup: ${LAST_BACKUP}"

# 2. Verify backup size
LATEST_BACKUP=$(aws s3 ls s3://ios-system-backups/production/ | \
  sort -r | head -1 | awk '{print $4}')

BACKUP_SIZE=$(aws s3 ls "s3://ios-system-backups/production/${LATEST_BACKUP}" | \
  awk '{print $3}')

echo "Backup size: $((BACKUP_SIZE / 1024 / 1024)) MB"

# 3. Alert if backup failed (via Prometheus)
# Rule in prometheus-alerts.yml:
# - alert: BackupFailed
#   expr: time() - backup_last_success_timestamp > 86400
#   for: 1h
#   labels:
#     severity: critical
```

### Prevention
- [ ] Automated daily backups
- [ ] Monthly restore tests
- [ ] PITR enabled
- [ ] Multi-region backup replication
- [ ] Backup encryption enabled
- [ ] Backup retention policy (30 days)

### Escalation
- **Restore needed:** DBA approval
- **PITR restore:** Engineering Lead approval
- **Production restore:** CTO approval required

---

## RUNBOOK 8: Certificate Renewal

### Symptoms
- Certificate expiring soon (30 days warning)
- Certificate expired
- SSL/TLS errors
- Browser warnings

### Impact
- **Severity:** Critical (if expired)
- **User Impact:** Cannot access service
- **Business Impact:** Complete service outage

### Investigation Steps

**Check Certificate Status**
```bash
# Check certificate expiration
echo | openssl s_client -connect api.ios-system.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# Check days until expiration
echo | openssl s_client -connect api.ios-system.com:443 2>/dev/null | \
  openssl x509 -noout -enddate | \
  sed 's/notAfter=//' | \
  xargs -I {} date -d {} +%s | \
  awk '{print ($1 - systime()) / 86400 " days until expiration"}'

# Check all domains
for domain in api.ios-system.com www.ios-system.com grafana.ios-system.com; do
  echo "=== $domain ==="
  echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
    openssl x509 -noout -dates
done

# Check Kubernetes secrets
kubectl get secret -n ios-production tls-certificate -o json | \
  jq -r '.data["tls.crt"]' | \
  base64 -d | \
  openssl x509 -noout -dates
```

### Renewal Procedures

**Automatic Renewal (Let's Encrypt + cert-manager)**
```bash
# cert-manager should auto-renew 30 days before expiry

# 1. Check cert-manager status
kubectl get pods -n cert-manager

# 2. Check certificate resource
kubectl get certificate -n ios-production

# Expected output:
# NAME              READY   SECRET            AGE
# tls-certificate   True    tls-certificate   60d

# 3. Check renewal logs
kubectl logs -n cert-manager deployment/cert-manager | grep renewal

# 4. Force renewal if needed
kubectl delete certificate tls-certificate -n ios-production

# This will trigger immediate renewal

# 5. Wait for renewal
kubectl wait --for=condition=Ready \
  certificate/tls-certificate -n ios-production \
  --timeout=300s

# 6. Verify new certificate
kubectl get secret tls-certificate -n ios-production -o json | \
  jq -r '.data["tls.crt"]' | \
  base64 -d | \
  openssl x509 -noout -dates
```

**Manual Renewal (Let's Encrypt)**
```bash
# If automatic renewal fails

# 1. Install certbot
apt-get install -y certbot

# 2. Stop nginx temporarily (if using standalone)
kubectl scale deployment/nginx --replicas=0 -n ios-production

# 3. Generate new certificate
certbot certonly --standalone \
  -d api.ios-system.com \
  -d www.ios-system.com \
  -d grafana.ios-system.com \
  --non-interactive \
  --agree-tos \
  --email admin@ios-system.com

# 4. Create Kubernetes secret
kubectl create secret tls tls-certificate \
  --cert=/etc/letsencrypt/live/api.ios-system.com/fullchain.pem \
  --key=/etc/letsencrypt/live/api.ios-system.com/privkey.pem \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart nginx
kubectl scale deployment/nginx --replicas=3 -n ios-production

# 6. Verify
curl -I https://api.ios-system.com
```

**Vault PKI (Internal Certificates)**
```bash
# Renew internal service certificates via Vault

# 1. Check current certificate
vault read pki/cert/<serial_number>

# 2. Generate new certificate
vault write pki/issue/ios-system \
  common_name="ios-api.ios-production.svc.cluster.local" \
  ttl="8760h"  # 1 year

# 3. Save certificate and key
vault read -field=certificate pki/issue/ios-system > tls.crt
vault read -field=private_key pki/issue/ios-system > tls.key

# 4. Update Kubernetes secret
kubectl create secret tls internal-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 5. Restart affected services
kubectl rollout restart deployment/ios-api -n ios-production
```

**Wildcard Certificate**
```bash
# For *.ios-system.com

# 1. Use DNS challenge (required for wildcard)
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials ~/.secrets/cloudflare.ini \
  -d '*.ios-system.com' \
  -d ios-system.com \
  --non-interactive \
  --agree-tos \
  --email admin@ios-system.com

# 2. CloudFlare credentials file (~/.secrets/cloudflare.ini):
# dns_cloudflare_email = admin@ios-system.com
# dns_cloudflare_api_key = YOUR_API_KEY

# 3. Update Kubernetes secret
kubectl create secret tls wildcard-tls \
  --cert=/etc/letsencrypt/live/ios-system.com/fullchain.pem \
  --key=/etc/letsencrypt/live/ios-system.com/privkey.pem \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Update ingress to use wildcard cert
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["*.ios-system.com"],"secretName":"wildcard-tls"}]}}'
```

### Emergency Certificate Expired

**Quick Fix (Temporary Self-Signed)**
```bash
# ⚠️ Only use in emergency - will cause browser warnings

# 1. Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key \
  -out tls.crt \
  -subj "/CN=api.ios-system.com/O=IOS System"

# 2. Create Kubernetes secret
kubectl create secret tls emergency-tls \
  --cert=tls.crt \
  --key=tls.key \
  -n ios-production \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Update ingress
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["api.ios-system.com"],"secretName":"emergency-tls"}]}}'

# 4. Service is now accessible (with browser warning)

# 5. Immediately renew proper certificate
# Follow manual renewal procedure above

# 6. Replace emergency cert with proper cert
kubectl patch ingress ios-ingress -n ios-production -p \
  '{"spec":{"tls":[{"hosts":["api.ios-system.com"],"secretName":"tls-certificate"}]}}'
```

### Monitoring & Alerts

**Certificate Expiry Alerts**
```yaml
# Prometheus alert rule
groups:
  - name: certificate_alerts
    rules:
      - alert: CertificateExpiringSoon
        expr: |
          (
            probe_ssl_earliest_cert_expiry{job="blackbox"}
            - time()
          ) / 86400 < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificate expiring in {{ $value }} days"
          description: "Certificate for {{ $labels.instance }} expires in {{ $value }} days"
      
      - alert: CertificateExpired
        expr: |
          (
            probe_ssl_earliest_cert_expiry{job="blackbox"}
            - time()
          ) < 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Certificate expired!"
          description: "Certificate for {{ $labels.instance }} has expired"
```

**Monitoring Script**
```bash
#!/bin/bash
# check_certificates.sh
# Run daily via cron

DOMAINS="api.ios-system.com www.ios-system.com grafana.ios-system.com"
WARN_DAYS=30

for domain in $DOMAINS; do
    expiry=$(echo | openssl s_client -connect $domain:443 -servername $domain 2>/dev/null | \
        openssl x509 -noout -enddate | sed 's/notAfter=//')
    
    expiry_epoch=$(date -d "$expiry" +%s)
    now_epoch=$(date +%s)
    days_left=$(( ($expiry_epoch - $now_epoch) / 86400 ))
    
    echo "$domain: $days_left days until expiration"
    
    if [ $days_left -lt $WARN_DAYS ]; then
        # Send alert
        curl -X POST "$SLACK_WEBHOOK_URL" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"⚠️ Certificate Warning: $domain expires in $days_left days\"
            }"
    fi
done
```

### Prevention
- [ ] Automatic renewal enabled (cert-manager)
- [ ] 30-day expiry alerts configured
- [ ] 7-day expiry critical alerts
- [ ] Monthly certificate audit
- [ ] Document renewal procedures
- [ ] Test renewal in staging monthly

### Escalation
- **30 days before expiry:** DevOps team (automated)
- **7 days before expiry:** Engineering Lead
- **Expired:** Immediate page to on-call

---

**Продолжение следует...**

Создано 8 из 10 runbooks:
- ✅ API Down
- ✅ High Error Rate
- ✅ Database Issues
- ✅ Performance Degradation
- ✅ Cache Problems
- ✅ Deployment Rollback
- ✅ Database Backup & Restore
- ✅ Certificate Renewal

**Следующие runbooks:**
- Scaling Operations
- Security Incident

**Готовы продолжить финальные 2 runbooks?**