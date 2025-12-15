#!/bin/bash
# Backup Script для IOS System
# Автоматический backup базы данных и файлов

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   IOS SYSTEM - BACKUP SCRIPT${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Configuration
BACKUP_DIR="/opt/backups/ios-system"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Create backup directory
mkdir -p ${BACKUP_DIR}/{database,files,configs}

echo "Starting backup process..."
echo "Timestamp: ${TIMESTAMP}"
echo "Backup directory: ${BACKUP_DIR}"
echo ""

# ======================================
# DATABASE BACKUP
# ======================================
echo -e "${BLUE}[1/4] Backing up PostgreSQL database...${NC}"

DB_BACKUP_FILE="${BACKUP_DIR}/database/postgres_${TIMESTAMP}.sql.gz"

docker-compose exec -T postgres pg_dump \
    -U ${POSTGRES_USER} \
    -d ${POSTGRES_DB} \
    --format=custom \
    --compress=9 | gzip > ${DB_BACKUP_FILE}

if [ -f ${DB_BACKUP_FILE} ]; then
    DB_SIZE=$(du -h ${DB_BACKUP_FILE} | cut -f1)
    echo -e "${GREEN}✓ Database backup created: ${DB_BACKUP_FILE} (${DB_SIZE})${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

# ======================================
# REDIS BACKUP
# ======================================
echo -e "${BLUE}[2/4] Backing up Redis...${NC}"

REDIS_BACKUP_FILE="${BACKUP_DIR}/database/redis_${TIMESTAMP}.rdb"

docker-compose exec -T redis redis-cli --raw SAVE > /dev/null 2>&1
docker cp ios_redis:/data/dump.rdb ${REDIS_BACKUP_FILE}

if [ -f ${REDIS_BACKUP_FILE} ]; then
    REDIS_SIZE=$(du -h ${REDIS_BACKUP_FILE} | cut -f1)
    echo -e "${GREEN}✓ Redis backup created: ${REDIS_BACKUP_FILE} (${REDIS_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ Redis backup failed (not critical)${NC}"
fi

# ======================================
# FILES BACKUP
# ======================================
echo -e "${BLUE}[3/4] Backing up application files...${NC}"

FILES_BACKUP="${BACKUP_DIR}/files/files_${TIMESTAMP}.tar.gz"

# Backup important directories
tar -czf ${FILES_BACKUP} \
    --exclude='node_modules' \
    --exclude='dist' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='logs/*' \
    ./logs \
    ./certbot \
    ./uploads 2>/dev/null || true

if [ -f ${FILES_BACKUP} ]; then
    FILES_SIZE=$(du -h ${FILES_BACKUP} | cut -f1)
    echo -e "${GREEN}✓ Files backup created: ${FILES_BACKUP} (${FILES_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ Files backup failed (not critical)${NC}"
fi

# ======================================
# CONFIGURATION BACKUP
# ======================================
echo -e "${BLUE}[4/4] Backing up configurations...${NC}"

CONFIG_BACKUP="${BACKUP_DIR}/configs/config_${TIMESTAMP}.tar.gz"

tar -czf ${CONFIG_BACKUP} \
    .env \
    docker-compose.yml \
    nginx/ \
    prometheus/ 2>/dev/null || true

if [ -f ${CONFIG_BACKUP} ]; then
    CONFIG_SIZE=$(du -h ${CONFIG_BACKUP} | cut -f1)
    echo -e "${GREEN}✓ Config backup created: ${CONFIG_BACKUP} (${CONFIG_SIZE})${NC}"
else
    echo -e "${YELLOW}⚠ Config backup failed (not critical)${NC}"
fi

# ======================================
# UPLOAD TO S3 (Optional)
# ======================================
if [ ! -z "${AWS_ACCESS_KEY_ID}" ] && [ ! -z "${BACKUP_S3_BUCKET}" ]; then
    echo -e "${BLUE}Uploading to S3...${NC}"
    
    aws s3 cp ${DB_BACKUP_FILE} s3://${BACKUP_S3_BUCKET}/database/ || echo "S3 upload failed"
    aws s3 cp ${FILES_BACKUP} s3://${BACKUP_S3_BUCKET}/files/ || echo "S3 upload failed"
    aws s3 cp ${CONFIG_BACKUP} s3://${BACKUP_S3_BUCKET}/configs/ || echo "S3 upload failed"
    
    echo -e "${GREEN}✓ Uploaded to S3${NC}"
fi

# ======================================
# CLEANUP OLD BACKUPS
# ======================================
echo -e "${BLUE}Cleaning up old backups (older than ${RETENTION_DAYS} days)...${NC}"

find ${BACKUP_DIR}/database -name "*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR}/database -name "*.rdb" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR}/files -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find ${BACKUP_DIR}/configs -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

echo -e "${GREEN}✓ Cleanup complete${NC}"

# ======================================
# SUMMARY
# ======================================
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   BACKUP SUMMARY${NC}"
echo -e "${BLUE}================================================${NC}"

TOTAL_SIZE=$(du -sh ${BACKUP_DIR} | cut -f1)

echo "Backup completed successfully!"
echo "Timestamp: ${TIMESTAMP}"
echo "Location: ${BACKUP_DIR}"
echo "Total size: ${TOTAL_SIZE}"
echo ""

# Count backups
DB_COUNT=$(ls -1 ${BACKUP_DIR}/database/*.sql.gz 2>/dev/null | wc -l)
echo "Total database backups: ${DB_COUNT}"
echo ""

echo -e "${GREEN}✓ All backups completed successfully!${NC}"

# Send notification (optional)
if [ ! -z "${SLACK_WEBHOOK}" ]; then
    curl -X POST ${SLACK_WEBHOOK} \
        -H 'Content-Type: application/json' \
        -d "{\"text\":\"✓ IOS System backup completed: ${TIMESTAMP}\"}" \
        > /dev/null 2>&1
fi

exit 0
