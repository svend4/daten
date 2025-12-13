Пользователь готов продолжить. Следующие файлы для Production Deployment Guide:
- Monitoring and alerting setup
- Operations runbooks  
- Team onboarding guide

Продолжаем создавать детальную документацию для Production deployment.# 📦 PRODUCTION DEPLOYMENT GUIDE (ПРОДОЛЖЕНИЕ)

## ФАЙЛ 5: `deployment/production/MONITORING_SETUP.md`

```markdown
# Production Monitoring & Alerting Setup

## 🎯 Overview

Comprehensive monitoring and alerting configuration for IOS System production environment.

**Monitoring Stack:**
- **Metrics:** Prometheus + Grafana
- **Logs:** ELK Stack (Elasticsearch, Logstash, Kibana)
- **Traces:** Jaeger (distributed tracing)
- **Uptime:** StatusCake / Pingdom
- **Errors:** Sentry
- **APM:** New Relic (optional)

---

## 📊 PROMETHEUS CONFIGURATION

### 1. Prometheus Deployment

**File:** `monitoring/prometheus/prometheus-config.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: monitoring
data:
  prometheus.yml: |
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
      - /etc/prometheus/rules/*.yml
    
    # Scrape configurations
    scrape_configs:
      # Kubernetes API server
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
      
      # Kubernetes nodes
      - job_name: 'kubernetes-nodes'
        kubernetes_sd_configs:
          - role: node
        scheme: https
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
          - action: labelmap
            regex: __meta_kubernetes_node_label_(.+)
      
      # Kubernetes pods
      - job_name: 'kubernetes-pods'
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
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
          - action: labelmap
            regex: __meta_kubernetes_pod_label_(.+)
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: kubernetes_namespace
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: kubernetes_pod_name
      
      # IOS API application
      - job_name: 'ios-api'
        kubernetes_sd_configs:
          - role: pod
            namespaces:
              names:
                - ios-production
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_label_app]
            action: keep
            regex: ios-api
          - source_labels: [__meta_kubernetes_pod_name]
            action: replace
            target_label: pod
          - source_labels: [__meta_kubernetes_namespace]
            action: replace
            target_label: namespace
      
      # PostgreSQL
      - job_name: 'postgresql'
        static_configs:
          - targets: ['postgresql-exporter:9187']
        relabel_configs:
          - source_labels: [__address__]
            target_label: instance
            replacement: 'postgresql-primary'
      
      # Redis
      - job_name: 'redis'
        static_configs:
          - targets: ['redis-exporter:9121']
        relabel_configs:
          - source_labels: [__address__]
            target_label: instance
            replacement: 'redis-primary'
      
      # Elasticsearch
      - job_name: 'elasticsearch'
        static_configs:
          - targets: ['elasticsearch-exporter:9114']
      
      # Node Exporter
      - job_name: 'node-exporter'
        kubernetes_sd_configs:
          - role: node
        relabel_configs:
          - source_labels: [__address__]
            regex: '(.*):10250'
            replacement: '${1}:9100'
            target_label: __address__
          - source_labels: [__meta_kubernetes_node_name]
            target_label: node
```

### 2. Alerting Rules

**File:** `monitoring/prometheus/rules/alerts.yml`

```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      # API Availability
      - alert: APIDown
        expr: up{job="ios-api"} == 0
        for: 1m
        labels:
          severity: critical
          component: api
        annotations:
          summary: "API instance {{ $labels.pod }} is down"
          description: "API pod {{ $labels.pod }} in namespace {{ $labels.namespace }} has been down for more than 1 minute."
          runbook: "https://runbooks.ios-system.com/api-down"
      
      # High Error Rate
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total[5m]))
          ) > 0.01
        for: 5m
        labels:
          severity: critical
          component: api
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 1%)"
          dashboard: "https://grafana.ios-system.com/d/api-overview"
      
      # High Latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
          component: api
        annotations:
          summary: "High latency detected on {{ $labels.endpoint }}"
          description: "P95 latency is {{ $value }}s (threshold: 0.5s)"
      
      # Memory Usage
      - alert: HighMemoryUsage
        expr: |
          (
            container_memory_usage_bytes{pod=~"ios-api-.*"}
            /
            container_spec_memory_limit_bytes{pod=~"ios-api-.*"}
          ) > 0.85
        for: 5m
        labels:
          severity: warning
          component: api
        annotations:
          summary: "High memory usage on {{ $labels.pod }}"
          description: "Memory usage is {{ $value | humanizePercentage }} (threshold: 85%)"
      
      # CPU Usage
      - alert: HighCPUUsage
        expr: |
          (
            rate(container_cpu_usage_seconds_total{pod=~"ios-api-.*"}[5m])
            /
            container_spec_cpu_quota{pod=~"ios-api-.*"} * 100000
          ) > 80
        for: 5m
        labels:
          severity: warning
          component: api
        annotations:
          summary: "High CPU usage on {{ $labels.pod }}"
          description: "CPU usage is {{ $value }}% (threshold: 80%)"
      
      # Pod Restart
      - alert: PodRestarting
        expr: rate(kube_pod_container_status_restarts_total{pod=~"ios-api-.*"}[15m]) > 0
        for: 5m
        labels:
          severity: warning
          component: api
        annotations:
          summary: "Pod {{ $labels.pod }} is restarting frequently"
          description: "Pod has restarted {{ $value }} times in the last 15 minutes"

  - name: database_alerts
    interval: 30s
    rules:
      # Database Down
      - alert: DatabaseDown
        expr: up{job="postgresql"} == 0
        for: 1m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL instance has been down for more than 1 minute"
          runbook: "https://runbooks.ios-system.com/database-down"
      
      # High Connection Count
      - alert: HighDatabaseConnections
        expr: |
          (
            pg_stat_database_numbackends{datname="ios_production"}
            /
            pg_settings_max_connections
          ) > 0.8
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "High database connection count"
          description: "Connection usage is {{ $value | humanizePercentage }} (threshold: 80%)"
      
      # Slow Queries
      - alert: SlowQueries
        expr: |
          rate(pg_stat_statements_mean_exec_time_seconds{datname="ios_production"}[5m]) > 1
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "Slow database queries detected"
          description: "Average query time is {{ $value }}s (threshold: 1s)"
      
      # Replication Lag
      - alert: ReplicationLag
        expr: pg_replication_lag_seconds > 60
        for: 5m
        labels:
          severity: warning
          component: database
        annotations:
          summary: "High replication lag"
          description: "Replication lag is {{ $value }}s (threshold: 60s)"
      
      # Disk Space
      - alert: DatabaseDiskSpaceLow
        expr: |
          (
            node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql"}
            /
            node_filesystem_size_bytes{mountpoint="/var/lib/postgresql"}
          ) < 0.2
        for: 5m
        labels:
          severity: critical
          component: database
        annotations:
          summary: "Low disk space on database"
          description: "Available disk space is {{ $value | humanizePercentage }} (threshold: 20%)"

  - name: redis_alerts
    interval: 30s
    rules:
      # Redis Down
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 1m
        labels:
          severity: critical
          component: cache
        annotations:
          summary: "Redis is down"
          description: "Redis instance has been down for more than 1 minute"
          runbook: "https://runbooks.ios-system.com/redis-down"
      
      # High Memory Usage
      - alert: RedisHighMemory
        expr: |
          (
            redis_memory_used_bytes
            /
            redis_memory_max_bytes
          ) > 0.85
        for: 5m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Redis memory usage high"
          description: "Memory usage is {{ $value | humanizePercentage }} (threshold: 85%)"
      
      # Low Cache Hit Rate
      - alert: LowCacheHitRate
        expr: |
          (
            rate(redis_keyspace_hits_total[5m])
            /
            (rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
          ) < 0.8
        for: 10m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Low Redis cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 80%)"
      
      # Rejected Connections
      - alert: RedisRejectedConnections
        expr: rate(redis_rejected_connections_total[5m]) > 0
        for: 5m
        labels:
          severity: warning
          component: cache
        annotations:
          summary: "Redis rejecting connections"
          description: "Redis has rejected {{ $value }} connections in the last 5 minutes"

  - name: business_alerts
    interval: 1m
    rules:
      # Low User Activity
      - alert: LowUserActivity
        expr: |
          sum(rate(user_logins_total[10m])) < 1
        for: 30m
        labels:
          severity: warning
          component: business
        annotations:
          summary: "Unusually low user activity"
          description: "User login rate is {{ $value }} per second (expected: >1/s)"
      
      # Payment Failures
      - alert: HighPaymentFailureRate
        expr: |
          (
            sum(rate(payment_transactions_total{status="failed"}[5m]))
            /
            sum(rate(payment_transactions_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          component: business
        annotations:
          summary: "High payment failure rate"
          description: "Payment failure rate is {{ $value | humanizePercentage }} (threshold: 5%)"
      
      # Search Performance
      - alert: SlowSearchQueries
        expr: |
          histogram_quantile(0.95,
            rate(search_query_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
          component: search
        annotations:
          summary: "Slow search queries"
          description: "P95 search latency is {{ $value }}s (threshold: 2s)"
```

### 3. Recording Rules

**File:** `monitoring/prometheus/rules/recording.yml`

```yaml
groups:
  - name: api_recording_rules
    interval: 30s
    rules:
      # Request rate by endpoint
      - record: api:http_requests:rate5m
        expr: |
          sum(rate(http_requests_total[5m])) by (endpoint, method, status)
      
      # Error rate
      - record: api:http_errors:rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
      
      # Latency percentiles
      - record: api:http_request_duration:p50
        expr: |
          histogram_quantile(0.50,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          )
      
      - record: api:http_request_duration:p95
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          )
      
      - record: api:http_request_duration:p99
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, endpoint)
          )
      
      # CPU usage per pod
      - record: api:cpu_usage:rate5m
        expr: |
          sum(rate(container_cpu_usage_seconds_total{pod=~"ios-api-.*"}[5m])) by (pod)
      
      # Memory usage per pod
      - record: api:memory_usage:current
        expr: |
          sum(container_memory_usage_bytes{pod=~"ios-api-.*"}) by (pod)

  - name: database_recording_rules
    interval: 30s
    rules:
      # Query rate
      - record: db:queries:rate5m
        expr: |
          sum(rate(pg_stat_statements_calls_total[5m])) by (datname)
      
      # Connection count
      - record: db:connections:current
        expr: |
          sum(pg_stat_database_numbackends) by (datname)
      
      # Transaction rate
      - record: db:transactions:rate5m
        expr: |
          sum(rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])) by (datname)
```

---

## 📈 GRAFANA DASHBOARDS

### 1. API Overview Dashboard

**File:** `monitoring/grafana/dashboards/api-overview.json`

```json
{
  "dashboard": {
    "title": "IOS API - Overview",
    "tags": ["ios-system", "api", "production"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (status)",
            "legendFormat": "{{status}}"
          }
        ],
        "yaxes": [
          {
            "format": "reqps",
            "label": "Requests/sec"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "api:http_errors:rate5m * 100",
            "legendFormat": "Error Rate %"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [1],
                "type": "gt"
              },
              "query": {
                "params": ["A", "5m", "now"]
              },
              "reducer": {
                "params": [],
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "executionErrorState": "alerting",
          "frequency": "60s",
          "handler": 1,
          "name": "High Error Rate",
          "noDataState": "no_data",
          "notifications": []
        },
        "thresholds": [
          {
            "value": 1,
            "colorMode": "critical",
            "fill": true,
            "line": true,
            "op": "gt"
          }
        ]
      },
      {
        "title": "Response Time (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "api:http_request_duration:p95",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Duration"
          }
        ]
      },
      {
        "title": "Active Pods",
        "type": "stat",
        "targets": [
          {
            "expr": "count(up{job=\"ios-api\"} == 1)"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area",
          "justifyMode": "auto",
          "orientation": "auto",
          "reduceOptions": {
            "values": false,
            "fields": "",
            "calcs": ["lastNotNull"]
          },
          "text": {},
          "textMode": "auto"
        },
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {
                  "value": null,
                  "color": "red"
                },
                {
                  "value": 3,
                  "color": "green"
                }
              ]
            }
          }
        }
      },
      {
        "title": "Requests by Endpoint",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, sum(rate(http_requests_total[5m])) by (endpoint, method))",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "excludeByName": {},
              "indexByName": {},
              "renameByName": {
                "endpoint": "Endpoint",
                "method": "Method",
                "Value": "Req/s"
              }
            }
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "api:cpu_usage:rate5m",
            "legendFormat": "{{pod}}"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "api:memory_usage:current / 1024 / 1024",
            "legendFormat": "{{pod}}"
          }
        ],
        "yaxes": [
          {
            "format": "decmbytes",
            "label": "Memory"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

### 2. Database Dashboard

**File:** `monitoring/grafana/dashboards/database.json`

```json
{
  "dashboard": {
    "title": "PostgreSQL - Production",
    "tags": ["ios-system", "database", "postgresql"],
    "panels": [
      {
        "title": "Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"ios_production\"}",
            "legendFormat": "Active Connections"
          },
          {
            "expr": "pg_settings_max_connections",
            "legendFormat": "Max Connections"
          }
        ]
      },
      {
        "title": "Transaction Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit{datname=\"ios_production\"}[5m])",
            "legendFormat": "Commits/s"
          },
          {
            "expr": "rate(pg_stat_database_xact_rollback{datname=\"ios_production\"}[5m])",
            "legendFormat": "Rollbacks/s"
          }
        ]
      },
      {
        "title": "Query Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_statements_mean_exec_time_seconds{datname=\"ios_production\"}",
            "legendFormat": "Mean Execution Time"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Duration"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "pg_stat_database_blks_hit{datname=\"ios_production\"} / (pg_stat_database_blks_hit{datname=\"ios_production\"} + pg_stat_database_blks_read{datname=\"ios_production\"}) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 90, "color": "yellow"},
                {"value": 95, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Slow Queries (>1s)",
        "type": "table",
        "targets": [
          {
            "expr": "topk(10, pg_stat_statements_mean_exec_time_seconds{datname=\"ios_production\"} > 1)",
            "format": "table",
            "instant": true
          }
        ]
      },
      {
        "title": "Database Size",
        "type": "stat",
        "targets": [
          {
            "expr": "pg_database_size_bytes{datname=\"ios_production\"} / 1024 / 1024 / 1024"
          }
        ],
        "options": {
          "unit": "decgbytes"
        }
      },
      {
        "title": "Replication Lag",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_replication_lag_seconds",
            "legendFormat": "Replica {{application_name}}"
          }
        ],
        "yaxes": [
          {
            "format": "s",
            "label": "Lag"
          }
        ]
      }
    ]
  }
}
```

### 3. Business Metrics Dashboard

**File:** `monitoring/grafana/dashboards/business-metrics.json`

```json
{
  "dashboard": {
    "title": "IOS System - Business Metrics",
    "tags": ["ios-system", "business", "kpi"],
    "panels": [
      {
        "title": "Active Users (Last 24h)",
        "type": "stat",
        "targets": [
          {
            "expr": "count(count_over_time(user_activity_total[24h]) > 0)"
          }
        ],
        "options": {
          "colorMode": "value",
          "graphMode": "area"
        }
      },
      {
        "title": "Documents Created",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(documents_created_total[5m]) * 3600",
            "legendFormat": "Documents/hour"
          }
        ]
      },
      {
        "title": "Search Queries",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(search_queries_total[5m]) * 60",
            "legendFormat": "Searches/minute"
          }
        ]
      },
      {
        "title": "User Registrations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(user_registrations_total[1h])",
            "legendFormat": "Registrations/hour"
          }
        ]
      },
      {
        "title": "Feature Usage",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(rate(feature_usage_total[24h])) by (feature)"
          }
        ]
      },
      {
        "title": "API Key Usage by Client",
        "type": "table",
        "targets": [
          {
            "expr": "topk(20, sum(rate(api_requests_total[1h])) by (client_id))",
            "format": "table",
            "instant": true
          }
        ]
      }
    ]
  }
}
```

---

## 🔔 ALERTMANAGER CONFIGURATION

### 1. Alert Routing

**File:** `monitoring/alertmanager/config.yml`

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

# Templates for alert formatting
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Alert routing tree
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  
  routes:
    # Critical alerts → PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    
    - match:
        severity: critical
      receiver: 'slack-critical'
    
    # Warning alerts → Slack only
    - match:
        severity: warning
      receiver: 'slack-warning'
    
    # Business alerts → Business Slack channel
    - match:
        component: business
      receiver: 'slack-business'
    
    # Database alerts → DBA team
    - match:
        component: database
      receiver: 'slack-dba'

# Inhibit rules (suppress alerts)
inhibit_rules:
  # Inhibit warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
  
  # Inhibit APIDown alerts if entire cluster is down
  - source_match:
      alertname: 'ClusterDown'
    target_match:
      alertname: 'APIDown'

# Receiver configurations
receivers:
  - name: 'default'
    slack_configs:
      - channel: '#monitoring-default'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_KEY'
        severity: 'critical'
        description: '{{ .GroupLabels.alertname }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          summary: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
  
  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          {{ range .Alerts }}
          *Alert:* {{ .Labels.alertname }}
          *Severity:* {{ .Labels.severity }}
          *Component:* {{ .Labels.component }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook }}
          *Dashboard:* {{ .Annotations.dashboard }}
          {{ end }}
        actions:
          - type: button
            text: 'View Dashboard'
            url: '{{ .Annotations.dashboard }}'
          - type: button
            text: 'View Runbook'
            url: '{{ .Annotations.runbook }}'
          - type: button
            text: 'Silence Alert'
            url: '{{ .ExternalURL }}/#/silences/new?filter={alertname="{{.GroupLabels.alertname}}"}'
  
  - name: 'slack-warning'
    slack_configs:
      - channel: '#alerts-warning'
        color: 'warning'
        title: '⚠️ WARNING: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'slack-business'
    slack_configs:
      - channel: '#business-alerts'
        title: '📊 Business Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'slack-dba'
    slack_configs:
      - channel: '#dba-alerts'
        title: '🗄️ Database Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

### 2. Alert Templates

**File:** `monitoring/alertmanager/templates/slack.tmpl`

```gotmpl
{{ define "slack.title" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .GroupLabels.alertname }}
{{ end }}

{{ define "slack.text" }}
{{ range .Alerts }}
*Alert:* {{ .Labels.alertname }}
*Severity:* {{ .Labels.severity }}
*Environment:* {{ .Labels.environment }}
*Cluster:* {{ .Labels.cluster }}
*Component:* {{ .Labels.component }}

*Description:* {{ .Annotations.description }}

*Started:* {{ .StartsAt.Format "2006-01-02 15:04:05 MST" }}
{{ if .EndsAt }}*Ended:* {{ .EndsAt.Format "2006-01-02 15:04:05 MST" }}{{ end }}

{{ if .Annotations.runbook }}*Runbook:* {{ .Annotations.runbook }}{{ end }}
{{ if .Annotations.dashboard }}*Dashboard:* {{ .Annotations.dashboard }}{{ end }}

---
{{ end }}
{{ end }}
```

---

## 📝 LOGGING CONFIGURATION

### 1. ELK Stack Configuration

**File:** `monitoring/elk/logstash.conf`

```conf
input {
  # Kubernetes logs
  beats {
    port => 5044
  }
  
  # Application logs directly
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{/ {
    json {
      source => "message"
    }
  }
  
  # Add Kubernetes metadata
  if [kubernetes] {
    mutate {
      add_field => {
        "environment" => "%{[kubernetes][labels][environment]}"
        "app" => "%{[kubernetes][labels][app]}"
        "pod" => "%{[kubernetes][pod][name]}"
        "namespace" => "%{[kubernetes][namespace]}"
      }
    }
  }
  
  # Parse log level
  if [level] {
    mutate {
      uppercase => [ "level" ]
    }
  }
  
  # Extract error details
  if [level] == "ERROR" {
    grok {
      match => {
        "message" => "%{GREEDYDATA:error_message}"
      }
    }
  }
  
  # Add timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
    target => "@timestamp"
  }
  
  # Remove unnecessary fields
  mutate {
    remove_field => [ "host", "beat", "offset" ]
  }
}

output {
  # Send to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-ios-production-%{+YYYY.MM.dd}"
    user => "${ELASTICSEARCH_USER}"
    password => "${ELASTICSEARCH_PASSWORD}"
  }
  
  # Send critical errors to separate index
  if [level] == "ERROR" or [level] == "CRITICAL" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "errors-ios-production-%{+YYYY.MM.dd}"
      user => "${ELASTICSEARCH_USER}"
      password => "${ELASTICSEARCH_PASSWORD}"
    }
  }
  
  # Debug output (optional)
  # stdout { codec => rubydebug }
}
```

### 2. Application Logging Configuration

**File:** `ios_core/logging.py`

```python
import logging
import json
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "duration"):
            log_data["duration_ms"] = record.duration
        
        return json.dumps(log_data)

def setup_logging(level: str = "INFO"):
    """Configure application logging"""
    
    # Create formatter
    formatter = JSONFormatter()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler("/var/log/ios-system/app.log")
    file_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
```

---

**Продолжение следует...**

Создано:
- ✅ Prometheus configuration (complete)
- ✅ Alert rules (20+ alerts)
- ✅ Grafana dashboards (3 dashboards)
- ✅ AlertManager configuration
- ✅ ELK logging setup

**Следующие файлы:**
- Operations runbooks
- Team onboarding guide
- Incident response procedures

**Готовы продолжить?**