Пользователь хочет продолжить с deployment инструкциями и финальной интеграцией. Это последняя часть комплексного руководства по Information Operating System. Мне нужно предоставить:

1. Deployment инструкции (пошаговое развертывание)
2. CI/CD конфигурация
3. Мониторинг и логирование
4. Backup и восстановление
5. Масштабирование
6. Интеграция с существующими проектами Max
7. Финальные рекомендации и roadmap

Давайте создадим исчерпывающее руководство.# ЧАСТЬ 11: DEPLOYMENT, МОНИТОРИНГ И ФИНАЛЬНАЯ ИНТЕГРАЦИЯ

## 11.1 Пошаговое развертывание

```bash
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
```

## 11.2 CI/CD конфигурация

```yaml
# .github/workflows/deploy.yml
# GitHub Actions для автоматического развертывания

name: IOS CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ========================================================================
  # ТЕСТИРОВАНИЕ
  # ========================================================================
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: |
        pytest tests/unit --cov=ios_core --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration --cov=api --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml

  # ========================================================================
  # СБОРКА DOCKER ОБРАЗА
  # ========================================================================
  build:
    name: Build Docker Image
    runs-on: ubuntu-latest
    needs: test
    
    permissions:
      contents: read
      packages: write
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=semver,pattern={{version}}
          type=semver,pattern={{major}}.{{minor}}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

  # ========================================================================
  # РАЗВЕРТЫВАНИЕ НА STAGING
  # ========================================================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    
    environment:
      name: staging
      url: https://staging.ios.example.com
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Deploy to staging server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_USERNAME }}
        key: ${{ secrets.STAGING_SSH_KEY }}
        script: |
          cd /opt/ios-system
          docker-compose pull
          docker-compose up -d
          docker-compose exec -T ios-api alembic upgrade head
    
    - name: Run smoke tests
      run: |
        curl -f https://staging.ios.example.com/health || exit 1

  # ========================================================================
  # РАЗВЕРТЫВАНИЕ НА PRODUCTION
  # ========================================================================
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    
    environment:
      name: production
      url: https://ios.example.com
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v3
    
    - name: Create backup on production
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USERNAME }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          /opt/ios-system/scripts/backup.sh
    
    - name: Deploy to production server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PRODUCTION_HOST }}
        username: ${{ secrets.PRODUCTION_USERNAME }}
        key: ${{ secrets.PRODUCTION_SSH_KEY }}
        script: |
          cd /opt/ios-system
          docker-compose pull
          docker-compose up -d
          docker-compose exec -T ios-api alembic upgrade head
    
    - name: Run health checks
      run: |
        sleep 30
        curl -f https://ios.example.com/health || exit 1
    
    - name: Notify on success
      uses: 8398a7/action-slack@v3
      if: success()
      with:
        status: success
        text: 'Production deployment successful! 🚀'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    
    - name: Notify on failure
      uses: 8398a7/action-slack@v3
      if: failure()
      with:
        status: failure
        text: 'Production deployment failed! ❌'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 11.3 Мониторинг и логирование

```yaml
# prometheus/prometheus.yml
# Prometheus конфигурация

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # IOS API
  - job_name: 'ios-api'
    static_configs:
      - targets: ['ios-api:8000']
    metrics_path: '/metrics'
  
  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
  
  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
  
  # Node Exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
  
  # Docker
  - job_name: 'docker'
    static_configs:
      - targets: ['cadvisor:8080']

# Alerting rules
rule_files:
  - 'alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

```yaml
# prometheus/alerts.yml
# Alert правила

groups:
  - name: ios_alerts
    interval: 30s
    rules:
      # API недоступен
      - alert: APIDown
        expr: up{job="ios-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "IOS API is down"
          description: "API has been down for more than 1 minute"
      
      # Высокая нагрузка CPU
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for 5 minutes"
      
      # Высокое использование памяти
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 90% for 5 minutes"
      
      # Медленные запросы
      - alert: SlowQueries
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API queries detected"
          description: "95th percentile of request duration is above 2 seconds"
      
      # Много ошибок
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5% for 5 minutes"
      
      # База данных недоступна
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "Database has been down for more than 1 minute"
      
      # Диск заполнен
      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space is low"
          description: "Less than 10% disk space available"
```

```python
# api/metrics.py
# Prometheus метрики для IOS API

from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request
import time

# Счетчики запросов
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Длительность запросов
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Активные запросы
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently in progress',
    ['method', 'endpoint']
)

# Метрики IOS
ios_documents_total = Gauge(
    'ios_documents_total',
    'Total number of documents',
    ['domain']
)

ios_entities_total = Gauge(
    'ios_entities_total',
    'Total number of entities',
    ['domain', 'type']
)

ios_search_queries_total = Counter(
    'ios_search_queries_total',
    'Total number of search queries',
    ['domain', 'type']
)

ios_classification_duration_seconds = Histogram(
    'ios_classification_duration_seconds',
    'Document classification duration in seconds'
)

# Middleware для отслеживания метрик
async def metrics_middleware(request: Request, call_next):
    """Middleware для сбора метрик запросов"""
    
    method = request.method
    endpoint = request.url.path
    
    # Начать отслеживание
    http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status = response.status_code
        
        # Записать метрики
        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        duration = time.time() - start_time
        http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
        return response
    
    finally:
        # Завершить отслеживание
        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()


# Endpoint для метрик
@app.get("/metrics")
async def metrics():
    """Endpoint для Prometheus метрик"""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )


# Функции для обновления метрик IOS
def update_document_metrics(domain_name: str, count: int):
    """Обновить метрики документов"""
    ios_documents_total.labels(domain=domain_name).set(count)


def update_entity_metrics(domain_name: str, entity_type: str, count: int):
    """Обновить метрики сущностей"""
    ios_entities_total.labels(domain=domain_name, type=entity_type).set(count)


def record_search_query(domain_name: str, search_type: str):
    """Записать метрику поискового запроса"""
    ios_search_queries_total.labels(domain=domain_name, type=search_type).inc()


def record_classification_duration(duration: float):
    """Записать длительность классификации"""
    ios_classification_duration_seconds.observe(duration)
```

```python
# api/logging_config.py
# Конфигурация логирования

import logging
import logging.handlers
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON форматтер для структурированных логов"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Добавить exception если есть
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Добавить дополнительные поля
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration
        
        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO", log_file: str = "/app/logs/ios.log"):
    """Настроить логирование"""
    
    # Создать logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Console handler (обычный формат)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (JSON формат)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(JSONFormatter())
    
    # Добавить handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```

## 11.4 Backup и восстановление

```bash
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
```

```bash
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
```

## 11.5 Интеграция с существующими проектами

```kotlin
// Интеграция IOS с Android Knowledge Planner Pro

// app/src/main/java/com/example/knowledgeplanner/IOSIntegration.kt

package com.example.knowledgeplanner.integration

import com.example.ios.client.IOSClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class IOSIntegration(
    private val iosClient: IOSClient,
    private val localDatabase: KnowledgeDatabase
) {
    /**
     * Синхронизация локальной базы знаний с IOS
     */
    suspend fun syncWithIOS() {
        // 1. Загрузить новые документы в IOS
        val localDocuments = localDatabase.getUnsyncedDocuments()
        
        for (document in localDocuments) {
            val file = document.toFile()
            
            iosClient.uploadDocument(
                file = file,
                domainName = "Knowledge-Planner",
                title = document.title,
                tags = document.tags
            ).onSuccess {
                // Пометить как синхронизированный
                localDatabase.markAsSynced(document.id, it.docId)
            }
        }
        
        // 2. Получить обновления из IOS
        iosClient.search(
            query = "",
            domainName = "Knowledge-Planner",
            limit = 100
        ).onSuccess { response ->
            for (result in response.results) {
                if (!localDatabase.exists(result.docId)) {
                    // Загрузить новый документ
                    downloadAndStore(result.docId)
                }
            }
        }
        
        // 3. Синхронизировать граф знаний
        syncKnowledgeGraph()
    }
    
    /**
     * Синхронизация графа знаний
     */
    private suspend fun syncKnowledgeGraph() {
        // Получить сущности из IOS
        iosClient.listEntities("Knowledge-Planner").onSuccess { entities ->
            for (entity in entities) {
                localDatabase.insertOrUpdateEntity(entity)
            }
        }
        
        // Получить отношения
        // TODO: API для получения всех отношений
    }
    
    /**
     * Поиск с использованием IOS
     */
    suspend fun enhancedSearch(query: String): List<SearchResult> {
        val results = mutableListOf<SearchResult>()
        
        // 1. Локальный поиск
        val localResults = localDatabase.search(query)
        results.addAll(localResults)
        
        // 2. Поиск в IOS (семантический)
        iosClient.search(
            query = query,
            domainName = "Knowledge-Planner",
            searchType = "semantic"
        ).onSuccess { response ->
            results.addAll(response.results.map { it.toSearchResult() })
        }
        
        // 3. Дедупликация и ранжирование
        return results.distinctBy { it.id }.sortedByDescending { it.score }
    }
    
    /**
     * Рекомендации на основе графа знаний
     */
    suspend fun getRecommendations(documentId: String): List<DocumentResult> {
        // Найти связанные документы через граф знаний
        return iosClient.getRelatedEntities(
            domainName = "Knowledge-Planner",
            entityId = documentId
        ).map { entity ->
            // Преобразовать сущность в рекомендацию
            // TODO: Реализовать преобразование
            DocumentResult(...)
        }.getOrElse { emptyList() }
    }
}
```

Продолжить с финальной частью - production checklist и roadmap?