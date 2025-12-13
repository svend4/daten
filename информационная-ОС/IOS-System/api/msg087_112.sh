#!/bin/bash
# Restore script for IOS System
# Restores PostgreSQL from S3 backup

set -euo pipefail

# ============================================
# Configuration
# ============================================
BACKUP_DIR="/backups"
RESTORE_DIR="${BACKUP_DIR}/restore"

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
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${BACKUP_DIR}/restore_${TIMESTAMP}.log"

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

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Restore IOS System database from backup.

OPTIONS:
    -b, --backup-name NAME    Backup name to restore (e.g., ios_backup_20250115_120000)
    -l, --latest              Restore the latest backup
    -f, --file FILE           Restore from local file
    -h, --help                Show this help message

EXAMPLES:
    # Restore latest backup
    $0 --latest

    # Restore specific backup
    $0 --backup-name ios_backup_20250115_120000

    # Restore from local file
    $0 --file /path/to/backup.sql.gz
EOF
    exit 0
}

# ============================================
# Parse arguments
# ============================================
BACKUP_NAME=""
USE_LATEST=false
LOCAL_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--backup-name)
            BACKUP_NAME="$2"
            shift 2
            ;;
        -l|--latest)
            USE_LATEST=true
            shift
            ;;
        -f|--file)
            LOCAL_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# ============================================
# Validation
# ============================================
if [ -z "$BACKUP_NAME" ] && [ "$USE_LATEST" = false ] && [ -z "$LOCAL_FILE" ]; then
    error "Must specify --backup-name, --latest, or --file. Use --help for usage."
fi

# ============================================
# Create restore directory
# ============================================
mkdir -p "$RESTORE_DIR"

# ============================================
# Get backup file
# ============================================
if [ -n "$LOCAL_FILE" ]; then
    # Use local file
    if [ ! -f "$LOCAL_FILE" ]; then
        error "File not found: $LOCAL_FILE"
    fi
    
    RESTORE_FILE="$LOCAL_FILE"
    log "Using local file: $RESTORE_FILE"

elif [ "$USE_LATEST" = true ]; then
    # Get latest backup from S3
    log "Finding latest backup..."
    
    LATEST_BACKUP=$(aws s3 ls "s3://${S3_BUCKET}/postgresql/" \
        --region "$AWS_REGION" | \
        grep "ios_backup_.*\.sql\.gz" | \
        sort -r | \
        head -n 1 | \
        awk '{print $4}')
    
    if [ -z "$LATEST_BACKUP" ]; then
        error "No backups found in S3"
    fi
    
    log "Latest backup: $LATEST_BACKUP"
    BACKUP_NAME="${LATEST_BACKUP%.sql.gz}"
    
    # Download from S3
    RESTORE_FILE="${RESTORE_DIR}/${LATEST_BACKUP}"
    
    log "Downloading from S3..."
    aws s3 cp \
        "s3://${S3_BUCKET}/postgresql/${LATEST_BACKUP}" \
        "$RESTORE_FILE" \
        --region "$AWS_REGION" \
        || error "Failed to download backup from S3"

else
    # Download specific backup from S3
    log "Downloading backup: ${BACKUP_NAME}..."
    
    RESTORE_FILE="${RESTORE_DIR}/${BACKUP_NAME}.sql.gz"
    
    aws s3 cp \
        "s3://${S3_BUCKET}/postgresql/${BACKUP_NAME}.sql.gz" \
        "$RESTORE_FILE" \
        --region "$AWS_REGION" \
        || error "Failed to download backup from S3"
fi

# ============================================
# Verify backup file
# ============================================
log "Verifying backup file..."

if [ ! -f "$RESTORE_FILE" ]; then
    error "Backup file not found: $RESTORE_FILE"
fi

FILE_SIZE=$(du -h "$RESTORE_FILE" | cut -f1)
log "Backup file size: $FILE_SIZE"

# Test gzip integrity
gunzip -t "$RESTORE_FILE" || error "Backup file is corrupted"

log "Backup file verified successfully"

# ============================================
# Confirmation
# ============================================
log "============================================"
log "WARNING: This will DROP and RECREATE the database!"
log "Database: $DB_NAME on $DB_HOST:$DB_PORT"
log "Backup file: $RESTORE_FILE"
log "============================================"

read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# ============================================
# Stop application (optional)
# ============================================
log "Scaling down application..."

if command -v kubectl >/dev/null 2>&1; then
    kubectl scale deployment/ios-api --replicas=0 -n ios-system \
        || log "WARNING: Failed to scale down application"
    
    log "Waiting for pods to terminate..."
    sleep 10
fi

# ============================================
# Backup current database (safety)
# ============================================
log "Creating safety backup of current database..."

export PGPASSWORD

SAFETY_BACKUP="${RESTORE_DIR}/pre_restore_${TIMESTAMP}.sql.gz"

pg_dump \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --format=plain \
    | gzip -9 > "$SAFETY_BACKUP" \
    || log "WARNING: Safety backup failed"

log "Safety backup created: $SAFETY_BACKUP"

# ============================================
# Terminate existing connections
# ============================================
log "Terminating existing database connections..."

psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    || log "WARNING: Failed to terminate connections"

# ============================================
# Drop and recreate database
# ============================================
log "Dropping existing database..."

psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --command="DROP DATABASE IF EXISTS ${DB_NAME};" \
    || error "Failed to drop database"

log "Creating new database..."

psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="postgres" \
    --command="CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};" \
    || error "Failed to create database"

# ============================================
# Restore database
# ============================================
log "Restoring database from backup..."

gunzip -c "$RESTORE_FILE" | \
psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --single-transaction \
    || error "Database restore failed"

log "Database restored successfully"

# ============================================
# Verify restore
# ============================================
log "Verifying restore..."

TABLE_COUNT=$(psql \
    --host="$DB_HOST" \
    --port="$DB_PORT" \
    --username="$DB_USER" \
    --dbname="$DB_NAME" \
    --tuples-only \
    --command="SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

log "Table count: $TABLE_COUNT"

if [ "$TABLE_COUNT" -lt 1 ]; then
    error "Restore verification failed: no tables found"
fi

# ============================================
# Restart application
# ============================================
log "Scaling up application..."

if command -v kubectl >/dev/null 2>&1; then
    kubectl scale deployment/ios-api --replicas=3 -n ios-system \
        || log "WARNING: Failed to scale up application"
    
    log "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod \
        -l app=ios-api \
        -n ios-system \
        --timeout=300s \
        || log "WARNING: Pods not ready after 5 minutes"
fi

# ============================================
# Cleanup
# ============================================
log "Cleaning up temporary files..."

if [ "$LOCAL_FILE" = "" ]; then
    rm -f "$RESTORE_FILE"
fi

# ============================================
# Send notification
# ============================================
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    log "Sending Slack notification..."
    
    curl -X POST "$SLACK_WEBHOOK_URL" \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"✅ IOS Database Restored\",
            \"blocks\": [
                {
                    \"type\": \"section\",
                    \"text\": {
                        \"type\": \"mrkdwn\",
                        \"text\": \"*Database Restored*\n• Backup: ${BACKUP_NAME}\n• Tables: ${TABLE_COUNT}\n• Safety backup: ${SAFETY_BACKUP}\"
                    }
                }
            ]
        }" || log "WARNING: Slack notification failed"
fi

# ============================================
# Summary
# ============================================
log "============================================"
log "Restore completed successfully!"
log "Backup restored: ${BACKUP_NAME}"
log "Table count: $TABLE_COUNT"
log "Safety backup: $SAFETY_BACKUP"
log "Log file: $LOG_FILE"
log "============================================"

exit 0