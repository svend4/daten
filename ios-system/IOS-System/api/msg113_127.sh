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