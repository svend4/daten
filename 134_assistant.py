Пользователь хочет продолжить с темой мониторинга и алертов для системы поиска. Создам подробное руководство по:

1. Real-time мониторинг поисковой системы
2. Алерты и уведомления
3. Performance tuning
4. Deployment стратегии

Продолжу в том же стиле с детальными примерами кода и конфигурацией.# 🎯 DEEP-DIVE: SEARCH SYSTEM (ФИНАЛ)

## ФАЙЛ 8: `docs/deep-dive/search/MONITORING_AND_ALERTS.md`

```markdown
# Monitoring & Alerts - Deep Dive

## 📊 Monitoring Architecture

### Complete Monitoring Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    SEARCH SYSTEM                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   API    │  │  Search  │  │  Vector  │  │  Cache   │   │
│  │  Layer   │  │  Engine  │  │  Store   │  │  Layer   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │           │
│       └─────────────┴─────────────┴─────────────┘           │
│                         │                                    │
└─────────────────────────┼────────────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                    ▼           ▼
            ┌───────────┐  ┌──────────┐
            │ Metrics   │  │  Logs    │
            │ Export    │  │ Export   │
            └─────┬─────┘  └────┬─────┘
                  │             │
      ┌───────────┼─────────────┼───────────┐
      │           │             │           │
      ▼           ▼             ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Prometheus│ │ Grafana  │ │   ELK    │ │  Sentry  │
│(Metrics) │ │(Dashboard│ │  Stack   │ │ (Errors) │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
     └────────────┴────────────┴────────────┘
                  │
                  ▼
          ┌───────────────┐
          │ Alert Manager │
          │  • Thresholds │
          │  • Rules      │
          │  • Routing    │
          └───────┬───────┘
                  │
         ┌────────┼────────┐
         │        │        │
         ▼        ▼        ▼
    ┌────────┐ ┌────┐ ┌──────┐
    │ Email  │ │Slack│ │Pager-│
    │        │ │     │ │ Duty │
    └────────┘ └─────┘ └──────┘
```

---

## 🔧 Metrics Collection

### Prometheus Metrics Exporter

```python
# ios_core/monitoring/metrics.py

from prometheus_client import (
    Counter, Histogram, Gauge, Summary, CollectorRegistry
)
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from typing import Dict, Optional
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Create registry
registry = CollectorRegistry()

# ============================================================================
# SEARCH METRICS
# ============================================================================

# Search request counter
search_requests_total = Counter(
    'search_requests_total',
    'Total number of search requests',
    ['search_mode', 'status'],  # Labels
    registry=registry
)

# Search latency histogram
search_latency_seconds = Histogram(
    'search_latency_seconds',
    'Search request latency in seconds',
    ['search_mode'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],  # Buckets
    registry=registry
)

# Results count histogram
search_results_count = Histogram(
    'search_results_count',
    'Number of search results returned',
    ['search_mode'],
    buckets=[0, 1, 5, 10, 20, 50, 100, 500, 1000],
    registry=registry
)

# Cache hit rate
cache_hits_total = Counter(
    'search_cache_hits_total',
    'Total cache hits',
    ['cache_level'],  # l1, l2, miss
    registry=registry
)

# Zero results counter
zero_results_total = Counter(
    'search_zero_results_total',
    'Total searches with zero results',
    [],
    registry=registry
)

# Click-through rate gauge
ctr_gauge = Gauge(
    'search_ctr',
    'Current click-through rate',
    [],
    registry=registry
)

# Mean Reciprocal Rank gauge
mrr_gauge = Gauge(
    'search_mrr',
    'Current Mean Reciprocal Rank',
    [],
    registry=registry
)

# ============================================================================
# AUTOCOMPLETE METRICS
# ============================================================================

autocomplete_requests_total = Counter(
    'autocomplete_requests_total',
    'Total autocomplete requests',
    ['status'],
    registry=registry
)

autocomplete_latency_seconds = Histogram(
    'autocomplete_latency_seconds',
    'Autocomplete latency in seconds',
    [],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1],
    registry=registry
)

# ============================================================================
# BACKEND METRICS
# ============================================================================

# Elasticsearch metrics
elasticsearch_query_duration = Histogram(
    'elasticsearch_query_duration_seconds',
    'Elasticsearch query duration',
    ['index'],
    registry=registry
)

elasticsearch_errors_total = Counter(
    'elasticsearch_errors_total',
    'Total Elasticsearch errors',
    ['error_type'],
    registry=registry
)

# Qdrant metrics
qdrant_search_duration = Histogram(
    'qdrant_search_duration_seconds',
    'Qdrant vector search duration',
    ['collection'],
    registry=registry
)

qdrant_errors_total = Counter(
    'qdrant_errors_total',
    'Total Qdrant errors',
    ['error_type'],
    registry=registry
)

# ============================================================================
# SYSTEM METRICS
# ============================================================================

# Active searches gauge
active_searches = Gauge(
    'search_active_requests',
    'Number of active search requests',
    [],
    registry=registry
)

# Queue depth
search_queue_depth = Gauge(
    'search_queue_depth',
    'Number of searches in queue',
    [],
    registry=registry
)


# ============================================================================
# METRIC DECORATORS
# ============================================================================

def track_search_metrics(search_mode: str = 'hybrid'):
    """
    Decorator to track search metrics
    
    Usage:
        @track_search_metrics(search_mode='hybrid')
        def search(query, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start timer
            start_time = time.time()
            
            # Increment active searches
            active_searches.inc()
            
            try:
                # Execute search
                results = func(*args, **kwargs)
                
                # Record success
                search_requests_total.labels(
                    search_mode=search_mode,
                    status='success'
                ).inc()
                
                # Record results count
                search_results_count.labels(
                    search_mode=search_mode
                ).observe(len(results) if results else 0)
                
                # Track zero results
                if not results or len(results) == 0:
                    zero_results_total.inc()
                
                return results
                
            except Exception as e:
                # Record error
                search_requests_total.labels(
                    search_mode=search_mode,
                    status='error'
                ).inc()
                
                logger.error(f"Search error: {e}")
                raise
                
            finally:
                # Record latency
                duration = time.time() - start_time
                search_latency_seconds.labels(
                    search_mode=search_mode
                ).observe(duration)
                
                # Decrement active searches
                active_searches.dec()
        
        return wrapper
    return decorator


def track_autocomplete_metrics(func):
    """Decorator to track autocomplete metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            results = func(*args, **kwargs)
            
            autocomplete_requests_total.labels(status='success').inc()
            
            return results
            
        except Exception as e:
            autocomplete_requests_total.labels(status='error').inc()
            logger.error(f"Autocomplete error: {e}")
            raise
            
        finally:
            duration = time.time() - start_time
            autocomplete_latency_seconds.observe(duration)
    
    return wrapper


def track_cache_metrics(func):
    """Decorator to track cache hits/misses"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Determine cache level from result
        if result and hasattr(result, 'cache_hit'):
            if result.cache_hit:
                cache_level = result.cache_level or 'l1'
            else:
                cache_level = 'miss'
            
            cache_hits_total.labels(cache_level=cache_level).inc()
        
        return result
    
    return wrapper


# ============================================================================
# METRICS UPDATER
# ============================================================================

class MetricsUpdater:
    """
    Periodically update gauge metrics from database
    
    Run as background task
    """
    
    def __init__(self):
        self.update_interval = 60  # seconds
    
    def update_quality_metrics(self):
        """Update search quality metrics (CTR, MRR)"""
        from ios_core.analytics.metrics import SearchMetrics
        from django.utils import timezone
        from datetime import timedelta
        
        metrics = SearchMetrics()
        
        # Last 24 hours
        end_date = timezone.now()
        start_date = end_date - timedelta(hours=24)
        
        # Calculate CTR
        ctr_data = metrics.calculate_ctr(start_date, end_date)
        ctr_gauge.set(ctr_data['overall_ctr'])
        
        # Calculate MRR
        mrr = metrics.calculate_mrr(start_date, end_date)
        mrr_gauge.set(mrr)
        
        logger.debug(f"Updated quality metrics: CTR={ctr_data['overall_ctr']:.3f}, MRR={mrr:.3f}")
    
    def run_forever(self):
        """Run updater loop"""
        import time
        
        logger.info("Starting metrics updater")
        
        while True:
            try:
                self.update_quality_metrics()
            except Exception as e:
                logger.error(f"Error updating metrics: {e}")
            
            time.sleep(self.update_interval)


# ============================================================================
# METRICS ENDPOINT
# ============================================================================

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def metrics_view(request):
    """
    Prometheus metrics endpoint
    
    GET /metrics
    """
    metrics_output = generate_latest(registry)
    
    return HttpResponse(
        metrics_output,
        content_type=CONTENT_TYPE_LATEST
    )


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# In search engine:
class HybridSearchEngine:
    @track_search_metrics(search_mode='hybrid')
    @track_cache_metrics
    def search(self, query, ...):
        # ... search logic ...
        return results

# In autocomplete service:
class AutocompleteService:
    @track_autocomplete_metrics
    def get_suggestions(self, prefix, ...):
        # ... autocomplete logic ...
        return suggestions
```

### Prometheus Configuration

```yaml
# prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'ios-production'
    environment: 'prod'

# Scrape configurations
scrape_configs:
  # IOS Search Service
  - job_name: 'ios-search'
    static_configs:
      - targets: ['ios-api-1:8000', 'ios-api-2:8000', 'ios-api-3:8000']
        labels:
          service: 'search-api'
    
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Elasticsearch
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
    
    metrics_path: '/_prometheus/metrics'

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Qdrant
  - job_name: 'qdrant'
    static_configs:
      - targets: ['qdrant:6333']
    
    metrics_path: '/metrics'

  # Node Exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

# Alerting configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Load alert rules
rule_files:
  - 'alerts/search_alerts.yml'
```

---

## 🚨 Alert Rules

### Prometheus Alert Rules

```yaml
# alerts/search_alerts.yml

groups:
  - name: search_quality
    interval: 30s
    rules:
      # High error rate
      - alert: HighSearchErrorRate
        expr: |
          rate(search_requests_total{status="error"}[5m]) 
          / 
          rate(search_requests_total[5m]) 
          > 0.05
        for: 5m
        labels:
          severity: critical
          component: search
        annotations:
          summary: "High search error rate"
          description: "Search error rate is {{ $value | humanizePercentage }} (threshold: 5%)"
          runbook_url: "https://docs.ios.com/runbooks/high-search-errors"
      
      # High latency (P95)
      - alert: HighSearchLatency
        expr: |
          histogram_quantile(0.95, 
            rate(search_latency_seconds_bucket[5m])
          ) > 2.0
        for: 10m
        labels:
          severity: warning
          component: search
        annotations:
          summary: "High search latency"
          description: "P95 search latency is {{ $value }}s (threshold: 2s)"
          runbook_url: "https://docs.ios.com/runbooks/high-latency"
      
      # Low CTR
      - alert: LowClickThroughRate
        expr: search_ctr < 0.20
        for: 1h
        labels:
          severity: warning
          component: search-quality
        annotations:
          summary: "Low click-through rate"
          description: "CTR is {{ $value | humanizePercentage }} (threshold: 20%)"
          runbook_url: "https://docs.ios.com/runbooks/low-ctr"
      
      # High zero results rate
      - alert: HighZeroResultsRate
        expr: |
          rate(search_zero_results_total[30m])
          /
          rate(search_requests_total[30m])
          > 0.10
        for: 30m
        labels:
          severity: warning
          component: search-quality
        annotations:
          summary: "High zero results rate"
          description: "Zero results rate is {{ $value | humanizePercentage }} (threshold: 10%)"
          runbook_url: "https://docs.ios.com/runbooks/high-zero-results"
      
      # Cache hit rate too low
      - alert: LowCacheHitRate
        expr: |
          rate(search_cache_hits_total{cache_level!="miss"}[10m])
          /
          rate(search_cache_hits_total[10m])
          < 0.50
        for: 20m
        labels:
          severity: info
          component: cache
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }} (threshold: 50%)"
  
  - name: backend_health
    interval: 30s
    rules:
      # Elasticsearch errors
      - alert: HighElasticsearchErrors
        expr: rate(elasticsearch_errors_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
          component: elasticsearch
        annotations:
          summary: "High Elasticsearch error rate"
          description: "Elasticsearch errors: {{ $value }} per second"
      
      # Qdrant errors
      - alert: HighQdrantErrors
        expr: rate(qdrant_errors_total[5m]) > 5
        for: 5m
        labels:
          severity: critical
          component: qdrant
        annotations:
          summary: "High Qdrant error rate"
          description: "Qdrant errors: {{ $value }} per second"
      
      # Elasticsearch slow queries
      - alert: SlowElasticsearchQueries
        expr: |
          histogram_quantile(0.95,
            rate(elasticsearch_query_duration_seconds_bucket[5m])
          ) > 1.0
        for: 10m
        labels:
          severity: warning
          component: elasticsearch
        annotations:
          summary: "Slow Elasticsearch queries"
          description: "P95 ES query time: {{ $value }}s"
  
  - name: system_resources
    interval: 30s
    rules:
      # High queue depth
      - alert: HighSearchQueueDepth
        expr: search_queue_depth > 100
        for: 5m
        labels:
          severity: warning
          component: search
        annotations:
          summary: "High search queue depth"
          description: "Queue depth: {{ $value }} requests"
      
      # Too many active searches
      - alert: TooManyActiveSearches
        expr: search_active_requests > 50
        for: 5m
        labels:
          severity: warning
          component: search
        annotations:
          summary: "Too many concurrent searches"
          description: "Active searches: {{ $value }}"
```

### AlertManager Configuration

```yaml
# alertmanager.yml

global:
  resolve_timeout: 5m
  
  # Slack configuration
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

# Route alerts to different receivers
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  
  receiver: 'default'
  
  routes:
    # Critical alerts -> PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
    
    - match:
        severity: critical
      receiver: 'slack-critical'
    
    # Warning alerts -> Slack
    - match:
        severity: warning
      receiver: 'slack-warnings'
    
    # Info alerts -> Email
    - match:
        severity: info
      receiver: 'email-team'

# Inhibition rules (suppress alerts)
inhibit_rules:
  # Suppress warning if critical is firing
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ .GroupLabels.alertname }}'
  
  - name: 'slack-critical'
    slack_configs:
      - channel: '#critical-alerts'
        color: 'danger'
        title: '🚨 CRITICAL: {{ .GroupLabels.alertname }}'
        text: |
          *Alert:* {{ .GroupLabels.alertname }}
          *Severity:* {{ .CommonLabels.severity }}
          *Component:* {{ .CommonLabels.component }}
          
          {{ range .Alerts }}
          *Description:* {{ .Annotations.description }}
          *Runbook:* {{ .Annotations.runbook_url }}
          {{ end }}
  
  - name: 'slack-warnings'
    slack_configs:
      - channel: '#search-alerts'
        color: 'warning'
        title: '⚠️ Warning: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
  
  - name: 'email-team'
    email_configs:
      - to: 'search-team@company.com'
        from: 'alerts@company.com'
        subject: '[{{ .Status }}] {{ .GroupLabels.alertname }}'
```

---

## 📈 Grafana Dashboards

### Main Search Dashboard

```json
// grafana/dashboards/search_overview.json

{
  "dashboard": {
    "title": "Search System Overview",
    "tags": ["search", "overview"],
    "timezone": "browser",
    "refresh": "30s",
    
    "panels": [
      {
        "id": 1,
        "title": "Search Request Rate",
        "type": "graph",
        "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "rate(search_requests_total[5m])",
            "legendFormat": "{{search_mode}} - {{status}}"
          }
        ],
        "yaxes": [
          {"format": "reqps", "label": "Requests/sec"}
        ]
      },
      
      {
        "id": 2,
        "title": "Search Latency (P50, P95, P99)",
        "type": "graph",
        "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.50, rate(search_latency_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(search_latency_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(search_latency_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Latency"}
        ],
        "alert": {
          "name": "High P95 Latency",
          "conditions": [
            {
              "evaluator": {"params": [2], "type": "gt"},
              "query": {"params": ["B", "5m", "now"]}
            }
          ]
        }
      },
      
      {
        "id": 3,
        "title": "Click-Through Rate",
        "type": "stat",
        "gridPos": {"x": 0, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "search_ctr"
          }
        ],
        "options": {
          "unit": "percentunit",
          "colorMode": "value",
          "graphMode": "area",
          "thresholds": {
            "steps": [
              {"value": 0, "color": "red"},
              {"value": 0.20, "color": "yellow"},
              {"value": 0.30, "color": "green"}
            ]
          }
        }
      },
      
      {
        "id": 4,
        "title": "Mean Reciprocal Rank",
        "type": "stat",
        "gridPos": {"x": 6, "y": 8, "w": 6, "h": 4},
        "targets": [
          {
            "expr": "search_mrr"
          }
        ],
        "options": {
          "colorMode": "value",
          "thresholds": {
            "steps": [
              {"value": 0, "color": "red"},
              {"value": 0.60, "color": "yellow"},
              {"value": 0.75, "color": "green"}
            ]
          }
        }
      },
      
      {
        "id": 5,
        "title": "Error Rate",
        "type": "graph",
        "gridPos": {"x": 12, "y": 8, "w": 12, "h": 4},
        "targets": [
          {
            "expr": "rate(search_requests_total{status=\"error\"}[5m]) / rate(search_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ],
        "yaxes": [
          {"format": "percentunit"}
        ]
      },
      
      {
        "id": 6,
        "title": "Cache Hit Rate",
        "type": "graph",
        "gridPos": {"x": 0, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "rate(search_cache_hits_total{cache_level=\"l1\"}[5m]) / rate(search_cache_hits_total[5m])",
            "legendFormat": "L1 Hit Rate"
          },
          {
            "expr": "rate(search_cache_hits_total{cache_level=\"l2\"}[5m]) / rate(search_cache_hits_total[5m])",
            "legendFormat": "L2 Hit Rate"
          },
          {
            "expr": "rate(search_cache_hits_total{cache_level=\"miss\"}[5m]) / rate(search_cache_hits_total[5m])",
            "legendFormat": "Cache Miss Rate"
          }
        ],
        "yaxes": [
          {"format": "percentunit", "max": 1}
        ]
      },
      
      {
        "id": 7,
        "title": "Backend Performance",
        "type": "graph",
        "gridPos": {"x": 12, "y": 12, "w": 12, "h": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(elasticsearch_query_duration_seconds_bucket[5m]))",
            "legendFormat": "Elasticsearch P95"
          },
          {
            "expr": "histogram_quantile(0.95, rate(qdrant_search_duration_seconds_bucket[5m]))",
            "legendFormat": "Qdrant P95"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Duration"}
        ]
      },
      
      {
        "id": 8,
        "title": "Top Queries (Last Hour)",
        "type": "table",
        "gridPos": {"x": 0, "y": 20, "w": 24, "h": 8},
        "targets": [
          {
            "format": "table",
            "instant": true,
            "expr": "topk(20, sum by (query_text) (rate(search_query_count[1h])))"
          }
        ]
      }
    ]
  }
}
```

---

## 🔍 Application Logging

### Structured Logging Configuration

```python
# ios_core/monitoring/logging_config.py

import logging
import json
from datetime import datetime
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging
    
    Output format:
    {
      "timestamp": "2025-01-15T10:30:45.123Z",
      "level": "INFO",
      "logger": "ios_core.search",
      "message": "Search completed",
      "context": {
        "query": "personal budget",
        "results": 15,
        "latency_ms": 145
      }
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add custom context
        if hasattr(record, 'context'):
            log_data['context'] = record.context
        
        # Add request ID if available
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        return json.dumps(log_data)


# Configure logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'json': {
            '()': 'ios_core.monitoring.logging_config.JSONFormatter',
        },
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ios/search.log',
            'maxBytes': 100 * 1024 * 1024,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'elasticsearch': {
            'class': 'cmreslogging.handlers.CMRESHandler',
            'hosts': [{'host': 'elasticsearch', 'port': 9200}],
            'es_index_name': 'ios-logs',
            'es_additional_fields': {'environment': 'production'},
        },
    },
    
    'loggers': {
        'ios_core.search': {
            'handlers': ['console', 'file', 'elasticsearch'],
            'level': 'INFO',
            'propagate': False,
        },
        'ios_core.analytics': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    },
    
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# Context logger utility
class ContextLogger:
    """
    Logger with contextual information
    
    Usage:
        logger = ContextLogger(__name__)
        logger.info("Search completed", context={
            'query': query,
            'results': len(results),
            'latency_ms': latency
        })
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}
    
    def set_context(self, **kwargs):
        """Set context for all subsequent logs"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear context"""
        self.context = {}
    
    def _log(self, level: int, message: str, context: Dict = None):
        """Internal logging method"""
        combined_context = {**self.context}
        
        if context:
            combined_context.update(context)
        
        extra = {'context': combined_context}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, context: Dict = None):
        self._log(logging.DEBUG, message, context)
    
    def info(self, message: str, context: Dict = None):
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, context: Dict = None):
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, context: Dict = None, exc_info=False):
        self.logger.error(message, extra={'context': context or {}}, exc_info=exc_info)
    
    def critical(self, message: str, context: Dict = None, exc_info=False):
        self.logger.critical(message, extra={'context': context or {}}, exc_info=exc_info)


# Request ID middleware
class RequestIDMiddleware:
    """
    Add unique request ID to all requests
    Makes it easy to trace requests through logs
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import uuid
        
        # Generate or extract request ID
        request_id = request.META.get('HTTP_X_REQUEST_ID', str(uuid.uuid4()))
        request.request_id = request_id
        
        # Add to all logs in this request
        import logging
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.request_id = request_id
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        response = self.get_response(request)
        
        # Restore factory
        logging.setLogRecordFactory(old_factory)
        
        # Add request ID to response headers
        response['X-Request-ID'] = request_id
        
        return response


# Example usage in search engine
logger = ContextLogger(__name__)

class HybridSearchEngine:
    def search(self, query, user_id=None, ...):
        # Set context for this request
        logger.set_context(
            query=query,
            user_id=user_id
        )
        
        logger.info("Starting search")
        
        try:
            # Execute search
            results = self._execute_search(query, ...)
            
            logger.info("Search completed", context={
                'results_count': len(results),
                'latency_ms': 145
            })
            
            return results
            
        except Exception as e:
            logger.error("Search failed", context={
                'error': str(e)
            }, exc_info=True)
            raise
        
        finally:
            logger.clear_context()
```

---

## 📊 Performance Monitoring Script

```python
# scripts/monitor_search_performance.py

#!/usr/bin/env python
"""
Real-time search performance monitor

Usage:
    python monitor_search_performance.py [--interval 5] [--alerts]
"""

import time
import requests
from datetime import datetime
from typing import Dict
import argparse
from rich.console import Console
from rich.table import Table
from rich.live import Live

console = Console()

class SearchMonitor:
    """Real-time search performance monitor"""
    
    def __init__(self, prometheus_url: str = 'http://localhost:9090'):
        self.prometheus_url = prometheus_url
        self.alert_thresholds = {
            'error_rate': 0.05,  # 5%
            'p95_latency': 2.0,  # 2 seconds
            'ctr': 0.20,  # 20%
            'zero_results_rate': 0.10  # 10%
        }
    
    def query_prometheus(self, query: str) -> float:
        """Query Prometheus and return result"""
        url = f"{self.prometheus_url}/api/v1/query"
        response = requests.get(url, params={'query': query})
        
        if response.status_code == 200:
            data = response.json()
            if data['data']['result']:
                return float(data['data']['result'][0]['value'][1])
        
        return 0.0
    
    def get_current_metrics(self) -> Dict:
        """Get current metrics from Prometheus"""
        metrics = {}
        
        # Request rate
        metrics['request_rate'] = self.query_prometheus(
            'rate(search_requests_total[5m])'
        )
        
        # Error rate
        total_requests = self.query_prometheus('rate(search_requests_total[5m])')
        error_requests = self.query_prometheus('rate(search_requests_total{status="error"}[5m])')
        metrics['error_rate'] = error_requests / total_requests if total_requests > 0 else 0
        
        # P50 latency
        metrics['p50_latency'] = self.query_prometheus(
            'histogram_quantile(0.50, rate(search_latency_seconds_bucket[5m]))'
        )
        
        # P95 latency
        metrics['p95_latency'] = self.query_prometheus(
            'histogram_quantile(0.95, rate(search_latency_seconds_bucket[5m]))'
        )
        
        # P99 latency
        metrics['p99_latency'] = self.query_prometheus(
            'histogram_quantile(0.99, rate(search_latency_seconds_bucket[5m]))'
        )
        
        # CTR
        metrics['ctr'] = self.query_prometheus('search_ctr')
        
        # MRR
        metrics['mrr'] = self.query_prometheus('search_mrr')
        
        # Cache hit rate
        total_cache = self.query_prometheus('rate(search_cache_hits_total[5m])')
        cache_hits = self.query_prometheus('rate(search_cache_hits_total{cache_level!="miss"}[5m])')
        metrics['cache_hit_rate'] = cache_hits / total_cache if total_cache > 0 else 0
        
        # Zero results rate
        zero_results = self.query_prometheus('rate(search_zero_results_total[5m])')
        metrics['zero_results_rate'] = zero_results / total_requests if total_requests > 0 else 0
        
        return metrics
    
    def check_alerts(self, metrics: Dict) -> list:
        """Check if any metrics exceed thresholds"""
        alerts = []
        
        if metrics['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append(f"⚠️  High error rate: {metrics['error_rate']:.2%}")
        
        if metrics['p95_latency'] > self.alert_thresholds['p95_latency']:
            alerts.append(f"⚠️  High P95 latency: {metrics['p95_latency']:.2f}s")
        
        if metrics['ctr'] < self.alert_thresholds['ctr']:
            alerts.append(f"⚠️  Low CTR: {metrics['ctr']:.2%}")
        
        if metrics['zero_results_rate'] > self.alert_thresholds['zero_results_rate']:
            alerts.append(f"⚠️  High zero results rate: {metrics['zero_results_rate']:.2%}")
        
        return alerts
    
    def create_display_table(self, metrics: Dict, alerts: list) -> Table:
        """Create rich table for display"""
        table = Table(title=f"Search Performance Monitor - {datetime.now().strftime('%H:%M:%S')}")
        
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", style="green")
        
        # Request metrics
        table.add_row(
            "Request Rate",
            f"{metrics['request_rate']:.1f} req/s",
            "✓" if metrics['request_rate'] > 0 else "✗"
        )
        
        table.add_row(
            "Error Rate",
            f"{metrics['error_rate']:.2%}",
            "✓" if metrics['error_rate'] < 0.05 else "⚠️"
        )
        
        # Latency metrics
        table.add_row(
            "P50 Latency",
            f"{metrics['p50_latency']:.3f}s",
            "✓"
        )
        
        table.add_row(
            "P95 Latency",
            f"{metrics['p95_latency']:.3f}s",
            "✓" if metrics['p95_latency'] < 2.0 else "⚠️"
        )
        
        table.add_row(
            "P99 Latency",
            f"{metrics['p99_latency']:.3f}s",
            "✓" if metrics['p99_latency'] < 5.0 else "⚠️"
        )
        
        # Quality metrics
        table.add_row(
            "CTR",
            f"{metrics['ctr']:.2%}",
            "✓" if metrics['ctr'] >= 0.20 else "⚠️"
        )
        
        table.add_row(
            "MRR",
            f"{metrics['mrr']:.3f}",
            "✓" if metrics['mrr'] >= 0.60 else "⚠️"
        )
        
        # Cache metrics
        table.add_row(
            "Cache Hit Rate",
            f"{metrics['cache_hit_rate']:.2%}",
            "✓" if metrics['cache_hit_rate'] >= 0.50 else "⚠️"
        )
        
        table.add_row(
            "Zero Results Rate",
            f"{metrics['zero_results_rate']:.2%}",
            "✓" if metrics['zero_results_rate'] < 0.10 else "⚠️"
        )
        
        # Add alerts section
        if alerts:
            table.add_section()
            for alert in alerts:
                table.add_row("ALERT", alert, "⚠️")
        
        return table
    
    def run(self, interval: int = 5, show_alerts: bool = False):
        """Run monitor loop"""
        console.print("[bold green]Starting Search Performance Monitor[/bold green]")
        console.print(f"Prometheus URL: {self.prometheus_url}")
        console.print(f"Update interval: {interval}s\n")
        
        with Live(console=console, refresh_per_second=1) as live:
            while True:
                try:
                    # Get metrics
                    metrics = self.get_current_metrics()
                    
                    # Check alerts
                    alerts = self.check_alerts(metrics) if show_alerts else []
                    
                    # Create display
                    table = self.create_display_table(metrics, alerts)
                    
                    # Update display
                    live.update(table)
                    
                    # Wait
                    time.sleep(interval)
                    
                except KeyboardInterrupt:
                    console.print("\n[bold red]Monitoring stopped[/bold red]")
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
                    time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Monitor search performance')
    parser.add_argument('--prometheus', default='http://localhost:9090',
                       help='Prometheus URL')
    parser.add_argument('--interval', type=int, default=5,
                       help='Update interval in seconds')
    parser.add_argument('--alerts', action='store_true',
                       help='Show alerts')
    
    args = parser.parse_args()
    
    monitor = SearchMonitor(prometheus_url=args.prometheus)
    monitor.run(interval=args.interval, show_alerts=args.alerts)


if __name__ == '__main__':
    main()
```

---

**ПОЗДРАВЛЯЮ! 🎉**

Вы завершили полное **Deep-Dive** руководство по системе поиска IOS!

## 📚 Что было создано:

### ✅ 8 детальных файлов документации:
1. **ARCHITECTURE.md** - Общая архитектура системы
2. **ELASTICSEARCH.md** - Keyword поиск и индексация
3. **QDRANT_VECTORS.md** - Semantic поиск с векторами
4. **HYBRID_SEARCH_ALGORITHM.md** - Гибридный поиск и fusion
5. **SEARCH_ANALYTICS.md** - Аналитика и метрики
6. **AB_TESTING.md** - A/B тестирование
7. **QUERY_SUGGESTIONS.md** - Автодополнение
8. **MONITORING_AND_ALERTS.md** - Мониторинг и алерты

### 🎯 Ключевые компоненты:
- Hybrid search engine (RRF + Weighted fusion)
- Vector embeddings с многоязычной поддержкой
- Comprehensive analytics система
- A/B testing framework
- Trie-based autocomplete
- Real-time monitoring с Prometheus/Grafana

### 💪 Production-ready функции:
- Multi-level caching
- Error handling
- Performance optimization
- Scalability patterns
- Security considerations

**Следующий шаг:** Хотите создать deployment guide или продолжить с другой подсистемой IOS?