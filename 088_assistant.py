Пользователь готов продолжить. Следующие файлы:
- Monitoring configuration (Prometheus, Grafana)
- Backup & restore scripts
- Deployment documentation
- Runbooks

Продолжаю создавать файлы для Week 23-24: Production Deployment & Infrastructure.# 🚀 WEEK 23-24: PRODUCTION DEPLOYMENT (ПРОДОЛЖЕНИЕ)

## DAY 135-136: MONITORING & BACKUP

---

## ФАЙЛ 16: `monitoring/prometheus/prometheus.yml`

```yaml
# Prometheus Configuration for IOS System
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ios-production'
    environment: 'production'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

# Load rules
rule_files:
  - 'alerts.yml'

# Scrape configurations
scrape_configs:
  # ============================================
  # Prometheus itself
  # ============================================
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # ============================================
  # IOS API
  # ============================================
  - job_name: 'ios-api'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - ios-system
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: ios-api
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - source_labels: [__meta_kubernetes_namespace]
        target_label: kubernetes_namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: kubernetes_pod_name

  # ============================================
  # PostgreSQL
  # ============================================
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # ============================================
  # Redis
  # ============================================
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # ============================================
  # Elasticsearch
  # ============================================
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch-exporter:9114']

  # ============================================
  # Node Exporter
  # ============================================
  - job_name: 'node'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:9100'
        target_label: __address__

  # ============================================
  # cAdvisor (Container metrics)
  # ============================================
  - job_name: 'cadvisor'
    kubernetes_sd_configs:
      - role: node
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__address__]
        regex: '(.*):10250'
        replacement: '${1}:4194'
        target_label: __address__

  # ============================================
  # Kubernetes API Server
  # ============================================
  - job_name: 'kubernetes-apiservers'
    kubernetes_sd_configs:
      - role: endpoints
    scheme: https
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace, __meta_kubernetes_service_name, __meta_kubernetes_endpoint_port_name]
        action: keep
        regex: default;kubernetes;https
```

---

## ФАЙЛ 17: `monitoring/prometheus/alerts.yml`

```yaml
# Prometheus Alert Rules for IOS System
groups:
  # ============================================
  # API Health Alerts
  # ============================================
  - name: api_health
    interval: 30s
    rules:
      - alert: APIDown
        expr: up{job="ios-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API instance is down"
          description: "API instance {{ $labels.instance }} has been down for more than 1 minute."

      - alert: APIHighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API error rate"
          description: "API error rate is {{ $value | humanizePercentage }} over the last 5 minutes."

      - alert: APISlowResponse
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API response time is slow"
          description: "95th percentile response time is {{ $value }}s, exceeding 1s threshold."

      - alert: APIHighRequestRate
        expr: rate(http_requests_total[1m]) > 1000
        for: 2m
        labels:
          severity: info
        annotations:
          summary: "High API request rate"
          description: "Request rate is {{ $value }} req/s, which is unusually high."

  # ============================================
  # Database Alerts
  # ============================================
  - name: database
    interval: 30s
    rules:
      - alert: PostgresDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL instance has been down for more than 1 minute."

      - alert: PostgresHighConnections
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL connection usage is high"
          description: "Connection usage is {{ $value | humanizePercentage }}, approaching max connections."

      - alert: PostgresSlowQueries
        expr: rate(pg_stat_statements_mean_exec_time[5m]) > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL queries are slow"
          description: "Average query time is {{ $value }}ms, exceeding 1000ms threshold."

      - alert: PostgresDiskSpace
        expr: (pg_database_size_bytes / 1024 / 1024 / 1024) > 40
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PostgreSQL disk space is running low"
          description: "Database size is {{ $value }}GB, approaching storage limit."

  # ============================================
  # Redis Alerts
  # ============================================
  - name: redis
    interval: 30s
    rules:
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis instance has been down for more than 1 minute."

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage is high"
          description: "Redis memory usage is {{ $value | humanizePercentage }}."

      - alert: RedisRejectedConnections
        expr: rate(redis_rejected_connections_total[5m]) > 0
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Redis is rejecting connections"
          description: "Redis rejected {{ $value }} connections in the last 5 minutes."

  # ============================================
  # Elasticsearch Alerts
  # ============================================
  - name: elasticsearch
    interval: 30s
    rules:
      - alert: ElasticsearchDown
        expr: up{job="elasticsearch"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch is down"
          description: "Elasticsearch instance has been down for more than 1 minute."

      - alert: ElasticsearchClusterRed
        expr: elasticsearch_cluster_health_status{color="red"} == 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch cluster status is RED"
          description: "Elasticsearch cluster health is RED for more than 5 minutes."

      - alert: ElasticsearchDiskSpaceLow
        expr: elasticsearch_filesystem_data_available_bytes / elasticsearch_filesystem_data_size_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Elasticsearch disk space is low"
          description: "Available disk space is {{ $value | humanizePercentage }}."

  # ============================================
  # Container Alerts
  # ============================================
  - name: containers
    interval: 30s
    rules:
      - alert: ContainerCPUHigh
        expr: rate(container_cpu_usage_seconds_total{namespace="ios-system"}[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container CPU usage is high"
          description: "Container {{ $labels.pod }} CPU usage is {{ $value | humanizePercentage }}."

      - alert: ContainerMemoryHigh
        expr: container_memory_usage_bytes{namespace="ios-system"} / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container memory usage is high"
          description: "Container {{ $labels.pod }} memory usage is {{ $value | humanizePercentage }}."

      - alert: ContainerRestarting
        expr: rate(kube_pod_container_status_restarts_total{namespace="ios-system"}[15m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container is restarting frequently"
          description: "Container {{ $labels.pod }} has restarted {{ $value }} times in the last 15 minutes."

  # ============================================
  # Kubernetes Alerts
  # ============================================
  - name: kubernetes
    interval: 30s
    rules:
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total{namespace="ios-system"}[1h]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          description: "Pod {{ $labels.pod }} is crash looping."

      - alert: PodNotReady
        expr: kube_pod_status_phase{namespace="ios-system",phase!~"Running|Succeeded"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pod is not ready"
          description: "Pod {{ $labels.pod }} has been in {{ $labels.phase }} state for more than 5 minutes."

      - alert: DeploymentReplicasMismatch
        expr: kube_deployment_spec_replicas{namespace="ios-system"} != kube_deployment_status_replicas_available{namespace="ios-system"}
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Deployment replicas mismatch"
          description: "Deployment {{ $labels.deployment }} has {{ $value }} replicas mismatch."
```

---

## ФАЙЛ 18: `monitoring/grafana/provisioning/datasources/prometheus.yml`

```yaml
# Grafana Datasource Configuration
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
      queryTimeout: 60s
      httpMethod: POST
```

---

## ФАЙЛ 19: `monitoring/grafana/dashboards/api-overview.json`

```json
{
  "dashboard": {
    "title": "IOS API Overview",
    "tags": ["ios", "api", "overview"],
    "timezone": "browser",
    "schemaVersion": 16,
    "version": 1,
    "refresh": "30s",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"ios-api\"}[5m])",
            "legendFormat": "{{method}} {{endpoint}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "reqps", "label": "Requests/sec"},
          {"format": "short"}
        ]
      },
      {
        "id": 2,
        "title": "Response Time (p95)",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job=\"ios-api\"}[5m]))",
            "legendFormat": "{{endpoint}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration"},
          {"format": "short"}
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "rate(http_requests_total{job=\"ios-api\",status=~\"5..\"}[5m])",
            "legendFormat": "{{status}} {{endpoint}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "reqps", "label": "Errors/sec"},
          {"format": "short"}
        ]
      },
      {
        "id": 4,
        "title": "Active Connections",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "http_active_connections{job=\"ios-api\"}",
            "refId": "A"
          }
        ]
      },
      {
        "id": 5,
        "title": "CPU Usage",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{namespace=\"ios-system\",pod=~\"ios-api.*\"}[5m])",
            "legendFormat": "{{pod}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "percentunit", "label": "CPU"},
          {"format": "short"}
        ]
      },
      {
        "id": 6,
        "title": "Memory Usage",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "container_memory_usage_bytes{namespace=\"ios-system\",pod=~\"ios-api.*\"}",
            "legendFormat": "{{pod}}",
            "refId": "A"
          }
        ],
        "yaxes": [
          {"format": "bytes", "label": "Memory"},
          {"format": "short"}
        ]
      }
    ]
  }
}
```

---

## ФАЙЛ 20: `scripts/backup/backup.sh`

```bash
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
```

---

## ФАЙЛ 21: `scripts/backup/restore.sh`

```bash
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
```

---

**Продолжение следует...**

Создано:
- ✅ Prometheus configuration (metrics, alerting)
- ✅ Alert rules (API, database, Redis, Elasticsearch, K8s)
- ✅ Grafana datasource & dashboard
- ✅ Comprehensive backup script
- ✅ Comprehensive restore script

**Следующие файлы:**
- Deployment documentation
- Runbooks
- Week summary
- Final checklist

**Готовы завершить Week 23-24?**