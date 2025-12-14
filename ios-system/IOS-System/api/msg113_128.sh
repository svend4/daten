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