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