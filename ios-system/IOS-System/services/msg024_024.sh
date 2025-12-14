#!/bin/bash
# scripts/restore.sh
# Скрипт восстановления IOS из backup

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -lh /opt/ios-backups/*.tar.gz
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/opt/ios-restore"

echo "=== IOS Restore Script ==="
echo "Backup file: $BACKUP_FILE"

# Проверить существование файла
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Спросить подтверждение
read -p "This will overwrite current data. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# ============================================================================
# PREPARE
# ============================================================================

echo "Preparing for restore..."
mkdir -p $RESTORE_DIR
cd $RESTORE_DIR

# Остановить сервисы
echo "Stopping services..."
cd /opt/ios-system
docker-compose down

# ============================================================================
# EXTRACT BACKUP
# ============================================================================

echo "Extracting backup..."
tar -xzf $BACKUP_FILE -C $RESTORE_DIR
BACKUP_NAME=$(basename $BACKUP_FILE .tar.gz)
cd $RESTORE_DIR/$BACKUP_NAME

# ============================================================================
# RESTORE DATABASE
# ============================================================================

echo "Restoring database..."

# Запустить PostgreSQL
cd /opt/ios-system
docker-compose up -d postgres
sleep 10

# Удалить существующую базу и создать новую
docker-compose exec -T postgres psql -U ios_user -c "DROP DATABASE IF EXISTS ios_db;"
docker-compose exec -T postgres psql -U ios_user -c "CREATE DATABASE ios_db;"

# Восстановить данные
gunzip < $RESTORE_DIR/$BACKUP_NAME/database.sql.gz | \
    docker-compose exec -T postgres psql -U ios_user ios_db

echo "✓ Database restored"

# ============================================================================
# RESTORE IOS DATA
# ============================================================================

echo "Restoring IOS data..."
rm -rf /opt/ios-system/data/*
tar -xzf $RESTORE_DIR/$BACKUP_NAME/ios-data.tar.gz -C /opt/ios-system/data
echo "✓ IOS data restored"

# ============================================================================
# RESTORE CONFIGURATION
# ============================================================================

echo "Restoring configuration..."
cp $RESTORE_DIR/$BACKUP_NAME/.env /opt/ios-system/
cp -r $RESTORE_DIR/$BACKUP_NAME/config/* /opt/ios-system/config/
echo "✓ Configuration restored"

# ============================================================================
# START SERVICES
# ============================================================================

echo "Starting services..."
cd /opt/ios-system
docker-compose up -d
sleep 30

# ============================================================================
# VERIFY
# ============================================================================

echo "Verifying restore..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✓ Services are healthy"
else
    echo "✗ Services health check failed"
    exit 1
fi

# ============================================================================
# CLEANUP
# ============================================================================

echo "Cleaning up..."
rm -rf $RESTORE_DIR

echo "=== Restore completed successfully ==="