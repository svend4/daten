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