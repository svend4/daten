#!/bin/bash
# deploy.sh
# Скрипт автоматического развертывания IOS

set -e  # Остановить при ошибке

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     INFORMATION OPERATING SYSTEM - DEPLOYMENT SCRIPT           ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

DEPLOY_ENV=${1:-production}  # production, staging, development
PROJECT_DIR="/opt/ios-system"
BACKUP_DIR="/opt/ios-backups"
LOG_FILE="/var/log/ios-deployment.log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функции логирования
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a $LOG_FILE
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a $LOG_FILE
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a $LOG_FILE
}

# ============================================================================
# ПРОВЕРКА СИСТЕМНЫХ ТРЕБОВАНИЙ
# ============================================================================

check_system_requirements() {
    log_info "Проверка системных требований..."
    
    # Проверка ОС
    if [[ ! -f /etc/os-release ]]; then
        log_error "Неподдерживаемая операционная система"
        exit 1
    fi
    
    # Проверка Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Установите Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    log_info "✓ Docker установлен: $(docker --version)"
    
    # Проверка Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose не установлен"
        exit 1
    fi
    log_info "✓ Docker Compose установлен: $(docker-compose --version)"
    
    # Проверка Python (для инициализации)
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 не установлен"
        exit 1
    fi
    log_info "✓ Python установлен: $(python3 --version)"
    
    # Проверка доступного места на диске (минимум 10GB)
    AVAILABLE_SPACE=$(df -BG / | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        log_warn "Недостаточно места на диске. Доступно: ${AVAILABLE_SPACE}GB, рекомендуется: 10GB+"
    else
        log_info "✓ Доступно места на диске: ${AVAILABLE_SPACE}GB"
    fi
    
    # Проверка RAM (минимум 4GB)
    TOTAL_RAM=$(free -g | awk 'NR==2 {print $2}')
    if [ "$TOTAL_RAM" -lt 4 ]; then
        log_warn "Недостаточно RAM. Доступно: ${TOTAL_RAM}GB, рекомендуется: 4GB+"
    else
        log_info "✓ Доступно RAM: ${TOTAL_RAM}GB"
    fi
}

# ============================================================================
# СОЗДАНИЕ ДИРЕКТОРИЙ
# ============================================================================

create_directories() {
    log_info "Создание структуры директорий..."
    
    mkdir -p $PROJECT_DIR/{config,data,logs,backups,ssl,scripts}
    mkdir -p $PROJECT_DIR/data/{uploads,exports,ios-root}
    mkdir -p $BACKUP_DIR
    
    log_info "✓ Директории созданы"
}

# ============================================================================
# ГЕНЕРАЦИЯ КОНФИГУРАЦИИ
# ============================================================================

generate_config() {
    log_info "Генерация конфигурации для окружения: $DEPLOY_ENV..."
    
    # Генерация .env файла
    cat > $PROJECT_DIR/.env <<EOF
# IOS System Configuration - ${DEPLOY_ENV}
DEPLOY_ENV=${DEPLOY_ENV}

# API Settings
IOS_ROOT_PATH=/data/ios-root
SECRET_KEY=$(openssl rand -hex 32)
API_HOST=0.0.0.0
API_PORT=8000

# Database
POSTGRES_DB=ios_db
POSTGRES_USER=ios_user
POSTGRES_PASSWORD=$(openssl rand -hex 16)
DATABASE_URL=postgresql://ios_user:\${POSTGRES_PASSWORD}@postgres:5432/ios_db

# Redis
REDIS_URL=redis://redis:6379/0

# Search
ELASTICSEARCH_URL=http://elasticsearch:9200

# Monitoring
ENABLE_METRICS=true
GRAFANA_ADMIN_PASSWORD=$(openssl rand -hex 12)

# Email (опционально)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=

# Storage
MAX_UPLOAD_SIZE=100M
UPLOAD_DIR=/data/uploads
EXPORT_DIR=/data/exports

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/ios.log

# Feature Flags
ENABLE_WEBSOCKET=true
ENABLE_ANALYTICS=true
ENABLE_AUTO_BACKUP=true
EOF
    
    log_info "✓ Конфигурация сгенерирована: $PROJECT_DIR/.env"
}

# ============================================================================
# ЗАГРУЗКА КОДА
# ============================================================================

download_code() {
    log_info "Загрузка кода приложения..."
    
    # Если это development, использовать локальный код
    if [ "$DEPLOY_ENV" = "development" ]; then
        log_info "Development режим - использование локального кода"
        cp -r ../ios-system/* $PROJECT_DIR/
    else
        # В production - клонировать из репозитория
        if [ -d "$PROJECT_DIR/.git" ]; then
            log_info "Обновление существующего репозитория..."
            cd $PROJECT_DIR
            git pull origin main
        else
            log_info "Клонирование репозитория..."
            git clone https://github.com/your-org/ios-system.git $PROJECT_DIR
        fi
    fi
    
    log_info "✓ Код загружен"
}

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================================

initialize_database() {
    log_info "Инициализация базы данных..."
    
    # Запустить только PostgreSQL
    cd $PROJECT_DIR
    docker-compose up -d postgres
    
    # Подождать пока PostgreSQL запустится
    log_info "Ожидание запуска PostgreSQL..."
    sleep 10
    
    # Выполнить миграции
    docker-compose run --rm ios-api alembic upgrade head
    
    log_info "✓ База данных инициализирована"
}

# ============================================================================
# SSL СЕРТИФИКАТЫ
# ============================================================================

setup_ssl() {
    log_info "Настройка SSL сертификатов..."
    
    if [ "$DEPLOY_ENV" = "production" ]; then
        # Production: Let's Encrypt
        log_info "Получение Let's Encrypt сертификатов..."
        
        # Установить certbot если не установлен
        if ! command -v certbot &> /dev/null; then
            log_info "Установка certbot..."
            apt-get update && apt-get install -y certbot
        fi
        
        # Запросить сертификат
        read -p "Введите домен для SSL сертификата: " DOMAIN
        read -p "Введите email для Let's Encrypt: " EMAIL
        
        certbot certonly --standalone -d $DOMAIN --email $EMAIL --agree-tos -n
        
        # Скопировать сертификаты
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem $PROJECT_DIR/ssl/
        cp /etc/letsencrypt/live/$DOMAIN/privkey.pem $PROJECT_DIR/ssl/
        
        log_info "✓ SSL сертификаты получены"
    else
        # Development/Staging: Self-signed сертификаты
        log_info "Создание self-signed SSL сертификатов..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout $PROJECT_DIR/ssl/privkey.pem \
            -out $PROJECT_DIR/ssl/fullchain.pem \
            -subj "/C=DE/ST=Bavaria/L=Munich/O=IOS/CN=localhost"
        
        log_info "✓ Self-signed сертификаты созданы"
    fi
}

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

start_application() {
    log_info "Запуск приложения..."
    
    cd $PROJECT_DIR
    
    # Сборка образов
    log_info "Сборка Docker образов..."
    docker-compose build
    
    # Запуск всех сервисов
    log_info "Запуск сервисов..."
    docker-compose up -d
    
    # Подождать пока все запустится
    log_info "Ожидание запуска всех сервисов..."
    sleep 30
    
    # Проверка здоровья
    log_info "Проверка здоровья сервисов..."
    
    if curl -f http://localhost/health &> /dev/null; then
        log_info "✓ Приложение запущено успешно"
    else
        log_error "Приложение не запустилось. Проверьте логи: docker-compose logs"
        exit 1
    fi
}

# ============================================================================
# ИНИЦИАЛИЗАЦИЯ IOS
# ============================================================================

initialize_ios() {
    log_info "Инициализация IOS системы..."
    
    # Создать начального пользователя
    docker-compose exec -T ios-api python -c "
from api.auth import create_user
create_user('admin', 'admin')  # TODO: Изменить в production
print('✓ Пользователь admin создан')
"
    
    # Создать примерный домен
    docker-compose exec -T ios-api python -c "
from ios_core import IOSRoot
ios = IOSRoot('/data/ios-root')
domain = ios.create_domain('Demo', {'language': 'de', 'description': 'Demo domain'})
print('✓ Домен Demo создан')
"
    
    log_info "✓ IOS инициализирована"
}

# ============================================================================
# НАСТРОЙКА МОНИТОРИНГА
# ============================================================================

setup_monitoring() {
    log_info "Настройка мониторинга..."
    
    # Grafana dashboards
    log_info "Импорт Grafana dashboards..."
    
    # Подождать пока Grafana запустится
    sleep 10
    
    # Добавить Prometheus как источник данных
    curl -X POST -H "Content-Type: application/json" \
        -d '{
            "name":"Prometheus",
            "type":"prometheus",
            "url":"http://prometheus:9090",
            "access":"proxy",
            "isDefault":true
        }' \
        http://admin:${GRAFANA_ADMIN_PASSWORD}@localhost:3000/api/datasources
    
    log_info "✓ Мониторинг настроен"
}

# ============================================================================
# СОЗДАНИЕ BACKUP
# ============================================================================

create_backup() {
    log_info "Создание резервной копии..."
    
    BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/ios_backup_$BACKUP_DATE"
    
    mkdir -p $BACKUP_PATH
    
    # Backup базы данных
    docker-compose exec -T postgres pg_dump -U ios_user ios_db > $BACKUP_PATH/database.sql
    
    # Backup данных
    tar -czf $BACKUP_PATH/ios-data.tar.gz -C $PROJECT_DIR/data .
    
    # Backup конфигурации
    cp $PROJECT_DIR/.env $BACKUP_PATH/
    
    log_info "✓ Backup создан: $BACKUP_PATH"
}

# ============================================================================
# ВЫВОД ИНФОРМАЦИИ
# ============================================================================

print_info() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║              IOS УСПЕШНО РАЗВЕРНУТА!                           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Доступ к сервисам:"
    echo "  • API:       http://localhost/api"
    echo "  • Docs:      http://localhost/api/docs"
    echo "  • Grafana:   http://localhost:3000"
    echo ""
    echo "Учетные данные:"
    echo "  • API:       admin / admin (ИЗМЕНИТЕ!)"
    echo "  • Grafana:   admin / (см. .env файл)"
    echo ""
    echo "Управление:"
    echo "  • Логи:      docker-compose logs -f"
    echo "  • Остановка: docker-compose down"
    echo "  • Перезапуск: docker-compose restart"
    echo ""
    echo "Конфигурация: $PROJECT_DIR/.env"
    echo "Логи:         $LOG_FILE"
    echo ""
}

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

main() {
    log_info "Начало развертывания IOS..."
    
    check_system_requirements
    create_directories
    generate_config
    download_code
    setup_ssl
    initialize_database
    start_application
    initialize_ios
    setup_monitoring
    create_backup
    
    print_info
    
    log_info "Развертывание завершено успешно!"
}

# Запуск
main "$@"