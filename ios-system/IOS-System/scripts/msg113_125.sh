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