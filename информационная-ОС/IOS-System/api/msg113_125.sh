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