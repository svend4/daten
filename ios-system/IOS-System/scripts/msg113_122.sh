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