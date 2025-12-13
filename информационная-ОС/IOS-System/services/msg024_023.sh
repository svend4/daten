#!/bin/bash
# scripts/backup.sh
# Скрипт резервного копирования IOS

set -e

BACKUP_DIR="/opt/ios-backups"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ios_backup_$DATE"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

echo "=== IOS Backup Script ==="
echo "Backup path: $BACKUP_PATH"

# Создать директорию
mkdir -p $BACKUP_PATH

# ============================================================================
# BACKUP DATABASE
# ============================================================================

echo "Backing up PostgreSQL database..."
docker-compose exec -T postgres pg_dump -U ios_user ios_db | gzip > $BACKUP_PATH/database.sql.gz
echo "✓ Database backed up"

# ============================================================================
# BACKUP IOS DATA
# ============================================================================

echo "Backing up IOS data..."
tar -czf $BACKUP_PATH/ios-data.tar.gz -C /opt/ios-system/data .
echo "✓ IOS data backed up"

# ============================================================================
# BACKUP CONFIGURATION
# ============================================================================

echo "Backing up configuration..."
cp /opt/ios-system/.env $BACKUP_PATH/
cp -r /opt/ios-system/config $BACKUP_PATH/
echo "✓ Configuration backed up"

# ============================================================================
# BACKUP ELASTICSEARCH (если используется)
# ============================================================================

if docker ps | grep -q elasticsearch; then
    echo "Backing up Elasticsearch..."
    docker-compose exec -T elasticsearch \
        curl -X PUT "localhost:9200/_snapshot/ios_backup/$BACKUP_NAME?wait_for_completion=true"
    echo "✓ Elasticsearch backed up"
fi

# ============================================================================
# CREATE METADATA
# ============================================================================

cat > $BACKUP_PATH/metadata.json <<EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$DATE",
    "components": {
        "database": true,
        "ios_data": true,
        "configuration": true,
        "elasticsearch": $(docker ps | grep -q elasticsearch && echo true || echo false)
    },
    "size_mb": $(du -sm $BACKUP_PATH | cut -f1)
}
EOF

echo "✓ Metadata created"

# ============================================================================
# COMPRESS BACKUP
# ============================================================================

echo "Compressing backup..."
cd $BACKUP_DIR
tar -czf ${BACKUP_NAME}.tar.gz $BACKUP_NAME
rm -rf $BACKUP_NAME
echo "✓ Backup compressed"

# ============================================================================
# UPLOAD TO S3 (опционально)
# ============================================================================

if [ -n "$AWS_S3_BUCKET" ]; then
    echo "Uploading to S3..."
    aws s3 cp ${BACKUP_NAME}.tar.gz s3://$AWS_S3_BUCKET/ios-backups/
    echo "✓ Uploaded to S3"
fi

# ============================================================================
# CLEANUP OLD BACKUPS
# ============================================================================

echo "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "ios_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
echo "✓ Old backups cleaned up"

# ============================================================================
# VERIFY BACKUP
# ============================================================================

echo "Verifying backup..."
if tar -tzf ${BACKUP_NAME}.tar.gz > /dev/null; then
    echo "✓ Backup verified successfully"
    BACKUP_SIZE=$(du -h ${BACKUP_NAME}.tar.gz | cut -f1)
    echo "Backup size: $BACKUP_SIZE"
else
    echo "✗ Backup verification failed!"
    exit 1
fi

echo "=== Backup completed successfully ==="
echo "Backup location: $BACKUP_DIR/${BACKUP_NAME}.tar.gz"