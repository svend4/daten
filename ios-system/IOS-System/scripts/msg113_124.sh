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