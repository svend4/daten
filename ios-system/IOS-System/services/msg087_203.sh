#!/bin/bash
# Backup script for IOS System
# Backs up PostgreSQL, uploads to S3, and rotates old backups

set -euo pipefail

# ============================================
# Configuration
# ============================================
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="ios_backup_${TIMESTAMP}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Database
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-ios}
DB_NAME=${DB_NAME:-ios_production}
PGPASSWORD=${DB_PASSWORD}

# S3 Configuration
S3_BUCKET=${BACKUP_S3_BUCKET:-ios-system-backups}
AWS_REGION=${AWS_REGION:-us-east-1}

# Logging
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# ============================================
# Functions
# ============================================
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $*"
    exit 1
}

cleanup() {
    log "Cleaning up temporary files..."
    rm -f "${BACKUP_DIR}/${BACKUP_NAME}.sql"
    rm -f "${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
}

trap cleanup EXIT

# ============================================
# Check prerequisites
# ============================================
log "Starting backup process..."

command -v pg_dump >/dev/null 2>&1 || error "pg_dump not found"
command -v aws >/dev/null 2>&1 || error "aws cli not found"
command -v gzip >/dev/null 2>&1 || error "gzip not found"

# ============================================
# Create backup directory
# ============================================
mkdir -p "$BACKUP_DIR"

# ============================================
# Backup PostgreSQL
# ============================================
log "Backing up PostgreSQL database..."

export PGPASSWORD

pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --file="${BACKUP_DIR}/${BACKUP_NAME}.sql" \
    || error "PostgreSQL backup failed"

log "PostgreSQL backup completed: ${BACKUP_NAME}.sql"

# ============================================
# Compress backup
# ============================================
log "Compressing backup..."

gzip -9 "${BACKUP_DIR}/${BACKUP_NAME}.sql" \
    || error "Compression failed"

BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}.sql.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

log "Backup compressed: ${BACKUP_SIZE}"

# ============================================
# Upload to S3
# ============================================
log "Uploading to S3..."

aws s3 cp \
    "$BACKUP_FILE" \
    "s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz" \
    --region "$AWS_REGION" \
    --storage-class STANDARD_IA \
    || error "S3 upload failed"

log "Uploaded to S3: s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz"

# ============================================
# Backup metadata (schemas, users, etc)
# ============================================
log "Backing up database metadata..."

pg_dumpall \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --globals-only \
    --file="${BACKUP_DIR}/${BACKUP_NAME}_globals.sql" \
    || log "WARNING: Globals backup failed"

if [ -f "${BACKUP_DIR}/${BACKUP_NAME}_globals.sql" ]; then
    gzip -9 "${BACKUP_DIR}/${BACKUP_NAME}_globals.sql"
    
    aws s3 cp \
        "${BACKUP_DIR}/${BACKUP_NAME}_globals.sql.gz" \
        "s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}_globals.sql.gz" \
        --region "$AWS_REGION" \
        || log "WARNING: Globals upload failed"
    
    rm -f "${BACKUP_DIR}/${BACKUP_NAME}_globals.sql.gz"
fi

# ============================================
# Backup Elasticsearch indices
# ============================================
if command -v curl >/dev/null 2>&1; then
    log "Backing up Elasticsearch indices..."
    
    ELASTICSEARCH_URL=${ELASTICSEARCH_URL:-http://elasticsearch:9200}
    
    curl -X PUT "${ELASTICSEARCH_URL}/_snapshot/backup_repo/${BACKUP_NAME}?wait_for_completion=true" \
        -H 'Content-Type: application/json' \
        -d '{
            "indices": "*",
            "ignore_unavailable": true,
            "include_global_state": false
        }' || log "WARNING: Elasticsearch backup failed"
fi

# ============================================
# Backup Redis (if configured)
# ============================================
if [ -n "${REDIS_URL:-}" ]; then
    log "Backing up Redis..."
    
    redis-cli --rdb "${BACKUP_DIR}/${BACKUP_NAME}.rdb" \
        || log "WARNING: Redis backup failed"
    
    if [ -f "${BACKUP_DIR}/${BACKUP_NAME}.rdb" ]; then
        gzip -9 "${BACKUP_DIR}/${BACKUP_NAME}.rdb"
        
        aws s3 cp \
            "${BACKUP_DIR}/${BACKUP_NAME}.rdb.gz" \
            "s3://${S3_BUCKET}/redis/${BACKUP_NAME}.rdb.gz" \
            --region "$AWS_REGION" \
            || log "WARNING: Redis upload failed"
        
        rm -f "${BACKUP_DIR}/${BACKUP_NAME}.rdb.gz"
    fi
fi

# ============================================
# Cleanup local backups
# ============================================
log "Cleaning up local backups older than ${RETENTION_DAYS} days..."

find "$BACKUP_DIR" -name "ios_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
find "$BACKUP_DIR" -name "backup_*.log" -mtime +${RETENTION_DAYS} -delete

# ============================================
# Cleanup S3 backups
# ============================================
log "Cleaning up S3 backups older than ${RETENTION_DAYS} days..."

CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%s)

aws s3api list-objects-v2 \
    --bucket "$S3_BUCKET" \
    --prefix "postgresql/" \
    --query "Contents[?LastModified<'$(date -d @${CUTOFF_DATE} --iso-8601=seconds)'].Key" \
    --output text | \
while read -r key; do
    if [ -n "$key" ]; then
        aws s3 rm "s3://${S3_BUCKET}/${key}" || log "WARNING: Failed to delete ${key}"
        log "Deleted old backup: ${key}"
    fi
done

# ============================================
# Verify backup integrity
# ============================================
log "Verifying backup integrity..."

# Check if file exists in S3
aws s3 ls "s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz" \
    || error "Backup verification failed: file not found in S3"

# Check file size
S3_SIZE=$(aws s3api head-object \
    --bucket "$S3_BUCKET" \
    --key "postgresql/${BACKUP_NAME}.sql.gz" \
    --query ContentLength \
    --output text)

if [ "$S3_SIZE" -lt 1000 ]; then
    error "Backup verification failed: file too small (${S3_SIZE} bytes)"
fi

log "Backup verification successful: ${S3_SIZE} bytes"

# ============================================
# Send notification
# ============================================
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    log "Sending Slack notification..."
    
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"✅ IOS Backup Completed\",
            \"blocks\": [
                {
                    \"type\": \"section\",
                    \"text\": {
                        \"type\": \"mrkdwn\",
                        \"text\": \"*Backup Completed*\n• Name: ${BACKUP_NAME}\n• Size: ${BACKUP_SIZE}\n• S3: s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz\"
                    }
                }
            ]
        }" || log "WARNING: Slack notification failed"
fi

# ============================================
# Summary
# ============================================
log "============================================"
log "Backup completed successfully!"
log "Backup name: ${BACKUP_NAME}"
log "Backup size: ${BACKUP_SIZE}"
log "S3 location: s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz"
log "Log file: ${LOG_FILE}"
log "============================================"

exit 0