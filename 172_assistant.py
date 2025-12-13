Пользователь хочет продолжить с Task 9.2: Monitoring & Logging Setup. Это последняя часть спринтов 9-10 по подготовке к развертыванию. Мне нужно покрыть:

1. Monitoring setup (Prometheus, Grafana)
2. Logging setup (ELK stack или альтернативы)
3. Error tracking (Sentry)
4. Health checks и alerting
5. Metrics collection
6. Dashboard creation

Продолжаю в формате markdown с детальными конфигурациями и скриптами.## ФАЙЛ 19 (продолжение): Monitoring & Logging Setup

```markdown
# Phase Implementation Details (продолжение)

#### Task 9.2: Monitoring & Logging Setup
**Assignee:** DevOps Engineer + Backend Developer
**Time:** 4 days
**Priority:** Critical

**Prometheus Configuration:**

```yaml
# monitoring/prometheus/prometheus.yml

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
  - 'alerts/*.yml'

# Scrape configurations
scrape_configs:
  # Django application metrics
  - job_name: 'django'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Elasticsearch
  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch-exporter:9114']

  # Redis
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  # Nginx
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  # Node exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Cadvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

**Alert Rules:**

```yaml
# monitoring/prometheus/alerts/app_alerts.yml

groups:
  - name: application_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          rate(django_http_requests_total{status=~"5.."}[5m]) 
          / rate(django_http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%)"

      # Slow response times
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, 
            rate(django_http_request_duration_seconds_bucket[5m])
          ) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 response time is high"
          description: "P95 latency is {{ $value }}s (threshold: 1s)"

      # Low cache hit rate
      - alert: LowCacheHitRate
        expr: |
          rate(django_cache_hits_total[5m]) 
          / (rate(django_cache_hits_total[5m]) + rate(django_cache_misses_total[5m])) 
          < 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate is low"
          description: "Hit rate is {{ $value | humanizePercentage }} (threshold: 50%)"

      # Application down
      - alert: ApplicationDown
        expr: up{job="django"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Django application is down"
          description: "Application has been down for more than 2 minutes"

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (container_memory_usage_bytes{name=~"ios-app.*"} 
          / container_spec_memory_limit_bytes{name=~"ios-app.*"}) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container memory usage is high"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          rate(container_cpu_usage_seconds_total{name=~"ios-app.*"}[5m]) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container CPU usage is high"
          description: "CPU usage is {{ $value | humanizePercentage }}"

  - name: database_alerts
    interval: 30s
    rules:
      # Database down
      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL database is down"
          description: "Database has been down for more than 1 minute"

      # Too many connections
      - alert: TooManyDatabaseConnections
        expr: |
          pg_stat_database_numbackends{datname="ios_db"} 
          / pg_settings_max_connections > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection count is high"
          description: "Using {{ $value | humanizePercentage }} of max connections"

      # Slow queries
      - alert: SlowQueries
        expr: |
          rate(pg_stat_database_tup_fetched{datname="ios_db"}[5m]) 
          / rate(pg_stat_database_tup_returned{datname="ios_db"}[5m]) < 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High proportion of slow queries"
          description: "Query efficiency is {{ $value | humanizePercentage }}"

  - name: elasticsearch_alerts
    interval: 30s
    rules:
      # Elasticsearch down
      - alert: ElasticsearchDown
        expr: up{job="elasticsearch"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch cluster is down"
          description: "Elasticsearch has been down for more than 2 minutes"

      # Cluster health red
      - alert: ElasticsearchClusterRed
        expr: elasticsearch_cluster_health_status{color="red"} == 1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Elasticsearch cluster health is RED"
          description: "At least one primary shard is not allocated"

      # High JVM memory
      - alert: ElasticsearchHighJVMMemory
        expr: |
          elasticsearch_jvm_memory_used_bytes{area="heap"} 
          / elasticsearch_jvm_memory_max_bytes{area="heap"} > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Elasticsearch JVM memory is high"
          description: "Heap usage is {{ $value | humanizePercentage }}"

  - name: redis_alerts
    interval: 30s
    rules:
      # Redis down
      - alert: RedisDown
        expr: up{job="redis"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Redis is down"
          description: "Redis has been down for more than 2 minutes"

      # High memory usage
      - alert: RedisHighMemory
        expr: |
          redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage is high"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # Too many rejected connections
      - alert: RedisRejectedConnections
        expr: |
          rate(redis_rejected_connections_total[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Redis is rejecting connections"
          description: "{{ $value }} connections/sec are being rejected"
```

**Django Prometheus Metrics:**

```python
# search/middleware/metrics.py

"""
Prometheus metrics middleware
"""

from prometheus_client import Counter, Histogram, Gauge
from django.utils.deprecation import MiddlewareMixin
import time

# Request metrics
request_count = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
)

# Cache metrics
cache_hits = Counter(
    'django_cache_hits_total',
    'Total cache hits',
    ['cache_name']
)

cache_misses = Counter(
    'django_cache_misses_total',
    'Total cache misses',
    ['cache_name']
)

# Database metrics
db_query_count = Counter(
    'django_db_queries_total',
    'Total database queries',
    ['query_type']
)

db_query_duration = Histogram(
    'django_db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Search metrics
search_requests = Counter(
    'django_search_requests_total',
    'Total search requests',
    ['search_type']
)

search_duration = Histogram(
    'django_search_duration_seconds',
    'Search duration in seconds',
    ['search_type'],
    buckets=(0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0)
)

search_results = Histogram(
    'django_search_results_count',
    'Number of search results',
    ['search_type'],
    buckets=(0, 1, 5, 10, 25, 50, 100, 500, 1000)
)

# Active users
active_requests = Gauge(
    'django_active_requests',
    'Number of active requests'
)

class PrometheusMetricsMiddleware(MiddlewareMixin):
    """Middleware to collect Prometheus metrics"""
    
    def process_request(self, request):
        """Start timing request"""
        request._start_time = time.time()
        active_requests.inc()
    
    def process_response(self, request, response):
        """Record metrics after response"""
        if hasattr(request, '_start_time'):
            # Calculate duration
            duration = time.time() - request._start_time
            
            # Extract endpoint
            endpoint = self._get_endpoint(request)
            
            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            request_duration.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            active_requests.dec()
        
        return response
    
    def process_exception(self, request, exception):
        """Handle exceptions"""
        if hasattr(request, '_start_time'):
            active_requests.dec()
        
        endpoint = self._get_endpoint(request)
        request_count.labels(
            method=request.method,
            endpoint=endpoint,
            status=500
        ).inc()
    
    def _get_endpoint(self, request):
        """Extract endpoint from request"""
        if hasattr(request, 'resolver_match') and request.resolver_match:
            return request.resolver_match.view_name
        return request.path
```

```python
# search/views/metrics.py

"""
Prometheus metrics endpoint
"""

from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

@never_cache
@csrf_exempt
def metrics(request):
    """
    Prometheus metrics endpoint
    
    Exposes metrics in Prometheus format
    """
    metrics_output = generate_latest()
    return HttpResponse(
        metrics_output,
        content_type=CONTENT_TYPE_LATEST
    )
```

**Grafana Dashboard:**

```json
# monitoring/grafana/dashboards/ios-overview.json

{
  "dashboard": {
    "title": "IOS Search - Overview",
    "tags": ["ios", "search", "overview"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(django_http_requests_total[5m])) by (status)",
            "legendFormat": "HTTP {{status}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Response Time (P95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(django_http_request_duration_seconds_bucket[5m])) by (le, endpoint))",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(django_http_requests_total{status=~\"5..\"}[5m])) / sum(rate(django_http_requests_total[5m]))",
            "legendFormat": "Error Rate"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
      },
      {
        "id": 4,
        "title": "Cache Hit Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(django_cache_hits_total[5m])) / (sum(rate(django_cache_hits_total[5m])) + sum(rate(django_cache_misses_total[5m])))",
            "legendFormat": "Hit Rate"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
      },
      {
        "id": 5,
        "title": "Search Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(django_search_duration_seconds_bucket[5m])) by (le, search_type))",
            "legendFormat": "P95 - {{search_type}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16}
      },
      {
        "id": 6,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"ios_db\"}",
            "legendFormat": "Active Connections"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16}
      }
    ]
  }
}
```

**Structured Logging Configuration:**

```python
# ios_core/settings/logging.py

"""
Logging configuration for production
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file_app': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
            'maxBytes': 1024 * 1024 * 50,  # 50MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'file_search': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'search.log',
            'maxBytes': 1024 * 1024 * 100,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_app'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file_error', 'sentry'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['file_app'],
            'level': 'WARNING',
            'propagate': False,
        },
        'search': {
            'handlers': ['console', 'file_search', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'analytics': {
            'handlers': ['console', 'file_app'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file_app', 'file_error'],
        'level': 'INFO',
    },
}
```

**Sentry Configuration:**

```python
# ios_core/settings/sentry.py

"""
Sentry error tracking configuration
"""

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os

def init_sentry():
    """Initialize Sentry SDK"""
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            RedisIntegration(),
            CeleryIntegration(),
        ],
        
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # Adjust this value in production
        traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
        
        # Send 10% of errors for profiling
        profiles_sample_rate=float(os.environ.get('SENTRY_PROFILES_SAMPLE_RATE', '0.1')),
        
        # Environment
        environment=os.environ.get('ENVIRONMENT', 'production'),
        
        # Release tracking
        release=os.environ.get('RELEASE_VERSION', 'unknown'),
        
        # Filter out certain errors
        ignore_errors=[
            'Http404',
            'PermissionDenied',
        ],
        
        # Before send callback to add custom data
        before_send=before_send_callback,
    )

def before_send_callback(event, hint):
    """
    Callback to modify events before sending to Sentry
    
    Can filter, modify, or add context to events
    """
    # Add custom tags
    if 'request' in event:
        event['tags'] = event.get('tags', {})
        event['tags']['user_agent'] = event['request'].get('headers', {}).get('User-Agent', 'unknown')
    
    # Filter out noisy errors
    if 'exception' in event:
        for exception in event['exception']['values']:
            if 'ConnectionResetError' in str(exception.get('type', '')):
                return None  # Don't send to Sentry
    
    return event
```

**Log Aggregation with ELK (Optional):**

```yaml
# monitoring/elk/docker-compose.elk.yml

version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elk-elasticsearch
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elk_es_data:/usr/share/elasticsearch/data
    networks:
      - elk

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: elk-logstash
    ports:
      - "5000:5000"
      - "9600:9600"
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
    depends_on:
      - elasticsearch
    networks:
      - elk

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: elk-kibana
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch
    networks:
      - elk

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: elk-filebeat
    user: root
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ../logs:/logs:ro
    depends_on:
      - logstash
    networks:
      - elk

volumes:
  elk_es_data:

networks:
  elk:
    driver: bridge
```

```yaml
# monitoring/elk/filebeat/filebeat.yml

filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /logs/*.log
    json.keys_under_root: true
    json.add_error_key: true
    fields:
      service: ios-search
      environment: production

  - type: docker
    containers.ids: '*'
    processors:
      - add_docker_metadata: ~

output.logstash:
  hosts: ["logstash:5000"]

logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644
```

**Health Check Script:**

```python
# scripts/health_check.py

"""
Comprehensive health check script
"""

import requests
import sys
import json
from typing import Dict, List

class HealthChecker:
    """Health check utility"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results = []
    
    def check_api_health(self) -> bool:
        """Check API health endpoint"""
        try:
            response = requests.get(
                f"{self.base_url}/api/health/",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.results.append({
                    'check': 'API Health',
                    'status': 'PASS',
                    'details': data
                })
                return True
            else:
                self.results.append({
                    'check': 'API Health',
                    'status': 'FAIL',
                    'details': f'HTTP {response.status_code}'
                })
                return False
        
        except Exception as e:
            self.results.append({
                'check': 'API Health',
                'status': 'FAIL',
                'details': str(e)
            })
            return False
    
    def check_search_functionality(self) -> bool:
        """Check search works"""
        try:
            response = requests.post(
                f"{self.base_url}/api/search/",
                json={'query': 'test', 'page': 1},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.results.append({
                    'check': 'Search Functionality',
                    'status': 'PASS',
                    'details': f"{data.get('total', 0)} results"
                })
                return True
            else:
                self.results.append({
                    'check': 'Search Functionality',
                    'status': 'FAIL',
                    'details': f'HTTP {response.status_code}'
                })
                return False
        
        except Exception as e:
            self.results.append({
                'check': 'Search Functionality',
                'status': 'FAIL',
                'details': str(e)
            })
            return False
    
    def check_response_time(self) -> bool:
        """Check response times are acceptable"""
        import time
        
        try:
            start = time.time()
            response = requests.post(
                f"{self.base_url}/api/search/",
                json={'query': 'test', 'page': 1},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000  # ms
            
            if elapsed < 500:  # Under 500ms
                self.results.append({
                    'check': 'Response Time',
                    'status': 'PASS',
                    'details': f'{elapsed:.0f}ms'
                })
                return True
            else:
                self.results.append({
                    'check': 'Response Time',
                    'status': 'WARN',
                    'details': f'{elapsed:.0f}ms (slow)'
                })
                return True  # Warning, not failure
        
        except Exception as e:
            self.results.append({
                'check': 'Response Time',
                'status': 'FAIL',
                'details': str(e)
            })
            return False
    
    def run_all_checks(self) -> bool:
        """Run all health checks"""
        print("="*60)
        print("HEALTH CHECK")
        print("="*60)
        
        checks = [
            self.check_api_health,
            self.check_search_functionality,
            self.check_response_time,
        ]
        
        all_passed = True
        for check in checks:
            passed = check()
            if not passed:
                all_passed = False
        
        # Print results
        print("\nResults:")
        for result in self.results:
            status_symbol = {
                'PASS': '✓',
                'FAIL': '✗',
                'WARN': '⚠'
            }.get(result['status'], '?')
            
            print(f"{status_symbol} {result['check']}: {result['status']}")
            print(f"  Details: {result['details']}")
        
        print("="*60)
        
        if all_passed:
            print("✓ ALL CHECKS PASSED")
        else:
            print("✗ SOME CHECKS FAILED")
        
        print("="*60)
        
        return all_passed

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python health_check.py <base_url>")
        sys.exit(1)
    
    checker = HealthChecker(sys.argv[1])
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)
```

**Monitoring Docker Compose Addition:**

```yaml
# Add to docker-compose.prod.yml

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: ios-prometheus
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - ios-network

  # Grafana
  grafana:
    image: grafana/grafana:latest
    container_name: ios-grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - ios-network

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    container_name: ios-node-exporter
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    restart: unless-stopped
    networks:
      - ios-network

  # cAdvisor
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: ios-cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
    restart: unless-stopped
    networks:
      - ios-network

volumes:
  prometheus_data:
  grafana_data:
```

**Checklist:**
- [ ] Setup Prometheus
- [ ] Configure alert rules
- [ ] Setup Grafana dashboards
- [ ] Implement Django metrics
- [ ] Configure structured logging
- [ ] Setup Sentry error tracking
- [ ] Optional: Configure ELK stack
- [ ] Create health check scripts
- [ ] Test monitoring and alerting
- [ ] Document monitoring procedures

---

## 🎉 MVP PHASE 1 - COMPLETE!

### Final Sprint Summary (9-10):

✅ **Task 9.1: Production Infrastructure** (3 days)
- Production Dockerfile optimized
- Multi-stage builds
- Docker Compose for production
- Nginx reverse proxy with SSL
- Blue-green deployment strategy
- Automated deployment scripts

✅ **Task 9.2: Monitoring & Logging** (4 days)
- Prometheus metrics collection
- Grafana dashboards
- Alert rules and notifications
- Structured JSON logging
- Sentry error tracking
- Health check automation

### Overall MVP Progress: **100% Complete** 🎊

```
┌─────────────────────────────────────────────────┐
│     MVP PHASE 1 - FINAL STATUS                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  Infrastructure:    ████████████████████ 100%  │
│  Core Search:       ████████████████████ 100%  │
│  API Layer:         ████████████████████ 100%  │
│  Testing:           ████████████████████ 100%  │
│  Deployment:        ████████████████████ 100%  │
│  Monitoring:        ████████████████████ 100%  │
│                                                 │
│  ─────────────────────────────────────────      │
│  OVERALL:           ████████████████████ 100%  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

**Готов создать итоговый ФАЙЛ 20: LAUNCH CHECKLIST & NEXT PHASES?**