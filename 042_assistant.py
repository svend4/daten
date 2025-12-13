Пользователь подтвердил готовность начать реализацию Roadmap v2.0. Теперь мне нужно предоставить детальный план с конкретными файлами, кодом и инструкциями для начала Phase 1 (v1.1 - Production Excellence).

Начну с Week 17-18: Observability Stack, предоставив полную реализацию с кодом, конфигурациями и инструкциями по развертыванию.# 🚀 ROADMAP v2.0 - НАЧАЛО РЕАЛИЗАЦИИ

---

## 📋 PHASE 1: v1.1 - PRODUCTION EXCELLENCE

### WEEK 17-18: OBSERVABILITY STACK

---

## DAY 113-114: Distributed Tracing (Jaeger)

### Файл 44: `docker-compose.observability.yml`

```yaml
version: '3.8'

services:
  # ========================================================================
  # Jaeger - Distributed Tracing
  # ========================================================================
  jaeger:
    image: jaegertracing/all-in-one:1.52
    container_name: ios-jaeger
    restart: unless-stopped
    
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
      - METRICS_STORAGE_TYPE=prometheus
    
    ports:
      - "5775:5775/udp"   # Zipkin compact
      - "6831:6831/udp"   # Jaeger compact
      - "6832:6832/udp"   # Jaeger binary
      - "5778:5778"       # Serve configs
      - "16686:16686"     # UI
      - "14250:14250"     # gRPC
      - "14268:14268"     # HTTP
      - "14269:14269"     # Admin
      - "9411:9411"       # Zipkin
    
    networks:
      - ios-network
    
    volumes:
      - jaeger-data:/badger

  # ========================================================================
  # Elasticsearch - Logs & Search
  # ========================================================================
  elasticsearch:
    image: elasticsearch:8.11.3
    container_name: ios-elasticsearch
    restart: unless-stopped
    
    environment:
      - node.name=es01
      - cluster.name=ios-cluster
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
      - xpack.security.enabled=false
      - xpack.security.enrollment.enabled=false
    
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    
    ports:
      - "9200:9200"
      - "9300:9300"
    
    volumes:
      - es-data:/usr/share/elasticsearch/data
    
    networks:
      - ios-network
    
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ========================================================================
  # Logstash - Log Processing
  # ========================================================================
  logstash:
    image: logstash:8.11.3
    container_name: ios-logstash
    restart: unless-stopped
    
    environment:
      - "LS_JAVA_OPTS=-Xms512m -Xmx512m"
    
    ports:
      - "5044:5044"     # Beats input
      - "9600:9600"     # Monitoring
      - "5000:5000/tcp" # TCP input
      - "5000:5000/udp" # UDP input
    
    volumes:
      - ./observability/logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./observability/logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - logstash-data:/usr/share/logstash/data
    
    networks:
      - ios-network
    
    depends_on:
      elasticsearch:
        condition: service_healthy

  # ========================================================================
  # Kibana - Log Visualization
  # ========================================================================
  kibana:
    image: kibana:8.11.3
    container_name: ios-kibana
    restart: unless-stopped
    
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - SERVER_NAME=ios-kibana
      - SERVER_HOST=0.0.0.0
    
    ports:
      - "5601:5601"
    
    networks:
      - ios-network
    
    depends_on:
      elasticsearch:
        condition: service_healthy
    
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:5601/api/status || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ========================================================================
  # Filebeat - Log Shipper
  # ========================================================================
  filebeat:
    image: elastic/filebeat:8.11.3
    container_name: ios-filebeat
    restart: unless-stopped
    
    user: root
    
    volumes:
      - ./observability/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - filebeat-data:/usr/share/filebeat/data
    
    networks:
      - ios-network
    
    depends_on:
      - logstash
    
    command: filebeat -e -strict.perms=false

  # ========================================================================
  # Sentry - Error Tracking
  # ========================================================================
  sentry-postgres:
    image: postgres:15-alpine
    container_name: ios-sentry-postgres
    restart: unless-stopped
    
    environment:
      - POSTGRES_USER=sentry
      - POSTGRES_PASSWORD=${SENTRY_DB_PASSWORD}
      - POSTGRES_DB=sentry
    
    volumes:
      - sentry-postgres-data:/var/lib/postgresql/data
    
    networks:
      - ios-network

  sentry-redis:
    image: redis:7-alpine
    container_name: ios-sentry-redis
    restart: unless-stopped
    
    volumes:
      - sentry-redis-data:/data
    
    networks:
      - ios-network

  sentry:
    image: sentry:latest
    container_name: ios-sentry
    restart: unless-stopped
    
    environment:
      - SENTRY_SECRET_KEY=${SENTRY_SECRET_KEY}
      - SENTRY_POSTGRES_HOST=sentry-postgres
      - SENTRY_DB_USER=sentry
      - SENTRY_DB_PASSWORD=${SENTRY_DB_PASSWORD}
      - SENTRY_REDIS_HOST=sentry-redis
    
    ports:
      - "9000:9000"
    
    volumes:
      - sentry-data:/var/lib/sentry/files
    
    networks:
      - ios-network
    
    depends_on:
      - sentry-postgres
      - sentry-redis

  sentry-worker:
    image: sentry:latest
    container_name: ios-sentry-worker
    restart: unless-stopped
    
    command: run worker
    
    environment:
      - SENTRY_SECRET_KEY=${SENTRY_SECRET_KEY}
      - SENTRY_POSTGRES_HOST=sentry-postgres
      - SENTRY_DB_USER=sentry
      - SENTRY_DB_PASSWORD=${SENTRY_DB_PASSWORD}
      - SENTRY_REDIS_HOST=sentry-redis
    
    networks:
      - ios-network
    
    depends_on:
      - sentry

  sentry-cron:
    image: sentry:latest
    container_name: ios-sentry-cron
    restart: unless-stopped
    
    command: run cron
    
    environment:
      - SENTRY_SECRET_KEY=${SENTRY_SECRET_KEY}
      - SENTRY_POSTGRES_HOST=sentry-postgres
      - SENTRY_DB_USER=sentry
      - SENTRY_DB_PASSWORD=${SENTRY_DB_PASSWORD}
      - SENTRY_REDIS_HOST=sentry-redis
    
    networks:
      - ios-network
    
    depends_on:
      - sentry

volumes:
  jaeger-data:
  es-data:
  logstash-data:
  filebeat-data:
  sentry-postgres-data:
  sentry-redis-data:
  sentry-data:

networks:
  ios-network:
    external: true
```

---

### Файл 45: `observability/logstash/pipeline/logstash.conf`

```conf
# Logstash Pipeline Configuration

input {
  # Beats input (from Filebeat)
  beats {
    port => 5044
    codec => json
  }
  
  # TCP input for application logs
  tcp {
    port => 5000
    codec => json_lines
  }
  
  # UDP input for syslog
  udp {
    port => 5000
    type => syslog
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{.*\}$/ {
    json {
      source => "message"
      target => "parsed"
    }
  }
  
  # Add timestamp
  if [parsed][timestamp] {
    date {
      match => ["[parsed][timestamp]", "ISO8601"]
      target => "@timestamp"
    }
  }
  
  # Extract log level
  if [parsed][level] {
    mutate {
      add_field => { "log_level" => "%{[parsed][level]}" }
      uppercase => [ "log_level" ]
    }
  }
  
  # Extract service name
  if [parsed][service] {
    mutate {
      add_field => { "service_name" => "%{[parsed][service]}" }
    }
  }
  
  # Extract trace ID if present
  if [parsed][trace_id] {
    mutate {
      add_field => { "trace_id" => "%{[parsed][trace_id]}" }
    }
  }
  
  # Parse stack traces
  if [parsed][exc_info] {
    mutate {
      add_field => { "exception" => "%{[parsed][exc_info]}" }
    }
  }
  
  # Tag errors
  if [log_level] == "ERROR" or [log_level] == "CRITICAL" {
    mutate {
      add_tag => [ "error" ]
    }
  }
  
  # Tag slow requests
  if [parsed][duration] and [parsed][duration] > 1000 {
    mutate {
      add_tag => [ "slow_request" ]
    }
  }
  
  # GeoIP for IP addresses
  if [parsed][ip] {
    geoip {
      source => "[parsed][ip]"
      target => "geoip"
    }
  }
  
  # User agent parsing
  if [parsed][user_agent] {
    useragent {
      source => "[parsed][user_agent]"
      target => "user_agent"
    }
  }
}

output {
  # Send to Elasticsearch
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "ios-logs-%{+YYYY.MM.dd}"
    
    # Use document type based on log level
    document_type => "%{log_level}"
  }
  
  # Debug output (optional, comment out in production)
  # stdout {
  #   codec => rubydebug
  # }
  
  # Send errors to separate index
  if "error" in [tags] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "ios-errors-%{+YYYY.MM.dd}"
    }
  }
  
  # Send slow requests to separate index
  if "slow_request" in [tags] {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      index => "ios-slow-%{+YYYY.MM.dd}"
    }
  }
}
```

---

### Файл 46: `observability/filebeat/filebeat.yml`

```yaml
# Filebeat Configuration

filebeat.inputs:
  # Docker container logs
  - type: container
    enabled: true
    paths:
      - '/var/lib/docker/containers/*/*.log'
    
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"
      
      - decode_json_fields:
          fields: ["message"]
          target: "json"
          overwrite_keys: true
      
      - add_fields:
          target: ''
          fields:
            environment: production

# Processors
processors:
  - add_host_metadata:
      when.not.contains.tags: forwarded
  
  - add_cloud_metadata: ~
  
  - add_docker_metadata: ~

# Output to Logstash
output.logstash:
  hosts: ["logstash:5044"]
  
  # Load balancing
  loadbalance: true
  
  # Compression
  compression_level: 3

# Logging
logging.level: info
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
  permissions: 0644

# Monitoring
monitoring.enabled: true
monitoring.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

---

### Файл 47: `ios_core/observability/__init__.py`

```python
"""
Observability module - Tracing, Logging, Metrics
"""

from .tracing import setup_tracing, tracer, trace_async
from .logging import setup_logging, get_logger
from .metrics import setup_metrics, metrics

__all__ = [
    'setup_tracing',
    'tracer',
    'trace_async',
    'setup_logging',
    'get_logger',
    'setup_metrics',
    'metrics',
]
```

---

### Файл 48: `ios_core/observability/tracing.py`

```python
"""
Distributed Tracing with OpenTelemetry
"""

import logging
from functools import wraps
from typing import Optional, Callable, Any
from contextlib import asynccontextmanager

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from ..config import settings

logger = logging.getLogger(__name__)

# Global tracer
tracer: Optional[trace.Tracer] = None


def setup_tracing(service_name: str = "ios-system"):
    """
    Setup distributed tracing with Jaeger
    
    Usage:
        setup_tracing("ios-api")
    """
    global tracer
    
    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        "environment": settings.environment,
        "version": settings.version,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Create Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=settings.jaeger_agent_host,
        agent_port=settings.jaeger_agent_port,
    )
    
    # Add batch span processor
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Set global tracer provider
    trace.set_tracer_provider(provider)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Auto-instrument libraries
    _auto_instrument()
    
    logger.info(f"Tracing initialized: {service_name} -> {settings.jaeger_agent_host}")
    
    return tracer


def _auto_instrument():
    """Auto-instrument common libraries"""
    
    try:
        # FastAPI
        FastAPIInstrumentor.instrument()
        
        # SQLAlchemy
        SQLAlchemyInstrumentor().instrument()
        
        # Redis
        RedisInstrumentor().instrument()
        
        # HTTP Requests
        RequestsInstrumentor().instrument()
        
        logger.info("Auto-instrumentation complete")
        
    except Exception as e:
        logger.warning(f"Auto-instrumentation failed: {e}")


def trace_async(
    span_name: Optional[str] = None,
    attributes: Optional[dict] = None
):
    """
    Decorator for tracing async functions
    
    Usage:
        @trace_async("process_document")
        async def process_document(file_path: str):
            ...
    """
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not tracer:
                return await func(*args, **kwargs)
            
            # Determine span name
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            # Start span
            with tracer.start_as_current_span(name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function arguments as attributes
                if args:
                    span.set_attribute("args", str(args))
                if kwargs:
                    span.set_attribute("kwargs", str(kwargs))
                
                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Mark success
                    span.set_attribute("success", True)
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    span.record_exception(e)
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    
                    raise
        
        return wrapper
    return decorator


@asynccontextmanager
async def trace_context(
    span_name: str,
    attributes: Optional[dict] = None
):
    """
    Context manager for tracing code blocks
    
    Usage:
        async with trace_context("database_query", {"query": "SELECT ..."}):
            result = await db.execute(query)
    """
    
    if not tracer:
        yield
        return
    
    with tracer.start_as_current_span(span_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        try:
            yield span
            span.set_attribute("success", True)
            
        except Exception as e:
            span.record_exception(e)
            span.set_attribute("success", False)
            raise


class TracedClass:
    """
    Base class for auto-tracing all methods
    
    Usage:
        class MyService(TracedClass):
            async def process(self, data):
                # Automatically traced
                ...
    """
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        # Wrap all async methods
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            
            if (callable(attr) and 
                not attr_name.startswith('_') and
                asyncio.iscoroutinefunction(attr)):
                
                setattr(
                    cls,
                    attr_name,
                    trace_async(f"{cls.__name__}.{attr_name}")(attr)
                )
```

---

### Файл 49: `ios_core/observability/logging.py`

```python
"""
Structured Logging with JSON output
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from pythonjsonlogger import jsonlogger

from ..config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add service name
        log_record['service'] = settings.service_name
        
        # Add environment
        log_record['environment'] = settings.environment
        
        # Add version
        log_record['version'] = settings.version
        
        # Add trace context if available
        from opentelemetry import trace
        span = trace.get_current_span()
        if span:
            context = span.get_span_context()
            log_record['trace_id'] = format(context.trace_id, '032x')
            log_record['span_id'] = format(context.span_id, '016x')
        
        # Rename level to match ELK convention
        if 'levelname' in log_record:
            log_record['level'] = log_record.pop('levelname')


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    json_format: bool = True
):
    """
    Setup structured logging
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for file logging
        json_format: Use JSON format (for ELK)
    """
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        # JSON formatter for structured logging
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Standard formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    logging.info(
        "Logging configured",
        extra={
            'log_level': log_level,
            'json_format': json_format,
            'log_file': str(log_file) if log_file else None
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with name
    
    Usage:
        logger = get_logger(__name__)
        logger.info("Message", extra={'key': 'value'})
    """
    return logging.getLogger(name)


class StructuredLogger:
    """
    Wrapper for structured logging with context
    
    Usage:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id=123, ip="1.2.3.4")
    """
    
    def __init__(self, name: str, context: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log(self, level: int, message: str, **kwargs):
        """Log with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={**self.context, **kwargs})
    
    def with_context(self, **context) -> 'StructuredLogger':
        """Create new logger with additional context"""
        return StructuredLogger(
            self.logger.name,
            {**self.context, **context}
        )
```

---

### Файл 50: `ios_core/observability/metrics.py`

```python
"""
Prometheus Metrics
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    REGISTRY
)
from typing import Dict, Any

from ..config import settings


class Metrics:
    """Application metrics"""
    
    def __init__(self):
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Document processing metrics
        self.documents_processed_total = Counter(
            'documents_processed_total',
            'Total documents processed',
            ['domain', 'document_type']
        )
        
        self.document_processing_duration_seconds = Histogram(
            'document_processing_duration_seconds',
            'Document processing duration in seconds',
            ['domain']
        )
        
        self.classification_confidence = Histogram(
            'classification_confidence',
            'Document classification confidence',
            ['document_type']
        )
        
        # Search metrics
        self.search_requests_total = Counter(
            'search_requests_total',
            'Total search requests',
            ['search_type', 'domain']
        )
        
        self.search_duration_seconds = Histogram(
            'search_duration_seconds',
            'Search duration in seconds',
            ['search_type']
        )
        
        self.search_results_count = Histogram(
            'search_results_count',
            'Number of search results returned',
            ['search_type']
        )
        
        # Knowledge graph metrics
        self.entities_extracted_total = Counter(
            'entities_extracted_total',
            'Total entities extracted',
            ['entity_type', 'domain']
        )
        
        self.relations_created_total = Counter(
            'relations_created_total',
            'Total relations created',
            ['relation_type', 'domain']
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation']
        )
        
        self.db_query_duration_seconds = Histogram(
            'db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation']
        )
        
        self.db_connections_active = Gauge(
            'db_connections_active',
            'Active database connections'
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits'
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses'
        )
        
        # Task metrics
        self.tasks_queued_total = Counter(
            'tasks_queued_total',
            'Total tasks queued',
            ['task_type']
        )
        
        self.tasks_completed_total = Counter(
            'tasks_completed_total',
            'Total tasks completed',
            ['task_type', 'status']
        )
        
        self.task_duration_seconds = Histogram(
            'task_duration_seconds',
            'Task duration in seconds',
            ['task_type']
        )
        
        # System metrics
        self.system_info = Gauge(
            'system_info',
            'System information',
            ['version', 'environment']
        )
        
        # Set system info
        self.system_info.labels(
            version=settings.version,
            environment=settings.environment
        ).set(1)
    
    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration: float
    ):
        """Record HTTP request metrics"""
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_document_processed(
        self,
        domain: str,
        document_type: str,
        duration: float,
        confidence: float
    ):
        """Record document processing metrics"""
        self.documents_processed_total.labels(
            domain=domain,
            document_type=document_type
        ).inc()
        
        self.document_processing_duration_seconds.labels(
            domain=domain
        ).observe(duration)
        
        self.classification_confidence.labels(
            document_type=document_type
        ).observe(confidence)
    
    def record_search(
        self,
        search_type: str,
        domain: str,
        duration: float,
        results_count: int
    ):
        """Record search metrics"""
        self.search_requests_total.labels(
            search_type=search_type,
            domain=domain or "all"
        ).inc()
        
        self.search_duration_seconds.labels(
            search_type=search_type
        ).observe(duration)
        
        self.search_results_count.labels(
            search_type=search_type
        ).observe(results_count)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format"""
        return generate_latest(REGISTRY).decode('utf-8')


def setup_metrics() -> Metrics:
    """Setup metrics"""
    return Metrics()


# Global metrics instance
metrics = setup_metrics()
```

---

### Файл 51: `api/middleware/observability.py`

```python
"""
Observability middleware for FastAPI
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ios_core.observability import metrics, get_logger

logger = get_logger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for capturing metrics and logs
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        
        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log request
        logger.info(
            "HTTP request started",
            method=method,
            path=path,
            ip=client_ip,
            user_agent=user_agent
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics.record_http_request(
                method=method,
                endpoint=path,
                status=response.status_code,
                duration=duration
            )
            
            # Log response
            logger.info(
                "HTTP request completed",
                method=method,
                path=path,
                status=response.status_code,
                duration=duration,
                ip=client_ip
            )
            
            # Add response headers
            response.headers["X-Request-Duration"] = str(duration)
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record error metrics
            metrics.record_http_request(
                method=method,
                endpoint=path,
                status=500,
                duration=duration
            )
            
            # Log error
            logger.error(
                "HTTP request failed",
                method=method,
                path=path,
                error=str(e),
                duration=duration,
                ip=client_ip,
                exc_info=True
            )
            
            raise
```

---

### Файл 52: `api/routes/metrics.py`

```python
"""
Metrics endpoint for Prometheus
"""

from fastapi import APIRouter, Response

from ios_core.observability import metrics

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint
    
    Returns metrics in Prometheus exposition format
    """
    return Response(
        content=metrics.get_metrics(),
        media_type="text/plain"
    )
```

---

### Файл 53: `scripts/setup_observability.sh`

```bash
#!/bin/bash
# Setup observability stack

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         OBSERVABILITY STACK SETUP                          ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"

mkdir -p observability/logstash/pipeline
mkdir -p observability/logstash/config
mkdir -p observability/filebeat
mkdir -p observability/kibana/dashboards

echo -e "${GREEN}✓ Directories created${NC}"

# Generate secrets
echo -e "\n${YELLOW}Generating secrets...${NC}"

if [ ! -f .env.observability ]; then
    cat > .env.observability << EOF
# Observability Stack Configuration
SENTRY_SECRET_KEY=$(openssl rand -hex 32)
SENTRY_DB_PASSWORD=$(openssl rand -hex 16)

# Jaeger
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831

# Elasticsearch
ES_JAVA_OPTS=-Xms2g -Xmx2g

# Environment
ENVIRONMENT=production
VERSION=1.1.0
SERVICE_NAME=ios-system
EOF

    echo -e "${GREEN}✓ Secrets generated in .env.observability${NC}"
else
    echo -e "${YELLOW}⚠ .env.observability already exists${NC}"
fi

# Create Logstash config
cat > observability/logstash/config/logstash.yml << 'EOF'
http.host: "0.0.0.0"
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.hosts: ["http://elasticsearch:9200"]
EOF

# Start observability stack
echo -e "\n${YELLOW}Starting observability stack...${NC}"

docker-compose -f docker-compose.observability.yml up -d

# Wait for services
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"

sleep 30

# Check Elasticsearch
echo -e "\n${YELLOW}Checking Elasticsearch...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:9200/_cluster/health > /dev/null; then
        echo -e "${GREEN}✓ Elasticsearch ready${NC}"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Check Kibana
echo -e "\n${YELLOW}Checking Kibana...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:5601/api/status > /dev/null; then
        echo -e "${GREEN}✓ Kibana ready${NC}"
        break
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Create Kibana index patterns
echo -e "\n${YELLOW}Creating Kibana index patterns...${NC}"

curl -X POST "http://localhost:5601/api/saved_objects/index-pattern/ios-logs" \
  -H "kbn-xsrf: true" \
  -H "Content-Type: application/json" \
  -d '{
    "attributes": {
      "title": "ios-logs-*",
      "timeFieldName": "@timestamp"
    }
  }' 2>/dev/null && echo -e "${GREEN}✓ Index pattern created${NC}" || echo -e "${YELLOW}⚠ Index pattern may already exist${NC}"

# Setup Sentry
echo -e "\n${YELLOW}Setting up Sentry...${NC}"

# Run Sentry upgrade
docker-compose -f docker-compose.observability.yml run --rm sentry upgrade --noinput

echo -e "\n${GREEN}✓ Sentry configured${NC}"

# Print summary
echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║            OBSERVABILITY STACK READY                       ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

echo -e "\n${GREEN}Access URLs:${NC}"
echo "  Jaeger UI:        http://localhost:16686"
echo "  Kibana:           http://localhost:5601"
echo "  Elasticsearch:    http://localhost:9200"
echo "  Sentry:           http://localhost:9000"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "  1. Configure Sentry: http://localhost:9000"
echo "  2. Import Kibana dashboards"
echo "  3. Update application config with Sentry DSN"
echo "  4. Restart IOS System to enable tracing"

echo -e "\n${GREEN}Done!${NC}"
```

---

### Файл 54: `tests/observability/test_tracing.py`

```python
"""
Tests for distributed tracing
"""

import pytest
from unittest.mock import Mock, patch

from ios_core.observability.tracing import (
    setup_tracing,
    trace_async,
    trace_context
)


def test_setup_tracing():
    """Test tracing setup"""
    
    tracer = setup_tracing("test-service")
    
    assert tracer is not None


@pytest.mark.asyncio
async def test_trace_async_decorator():
    """Test async tracing decorator"""
    
    setup_tracing("test")
    
    @trace_async("test_function")
    async def test_func(x: int) -> int:
        return x * 2
    
    result = await test_func(5)
    
    assert result == 10


@pytest.mark.asyncio
async def test_trace_async_with_exception():
    """Test tracing with exception"""
    
    setup_tracing("test")
    
    @trace_async("test_error")
    async def test_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await test_func()


@pytest.mark.asyncio
async def test_trace_context():
    """Test trace context manager"""
    
    setup_tracing("test")
    
    async with trace_context("test_context", {"key": "value"}):
        # Code is traced
        pass
```

---

## 📋 ИНСТРУКЦИИ ПО РАЗВЕРТЫВАНИЮ

### Шаг 1: Подготовка

```bash
# Обновить requirements.txt
cat >> requirements.txt << 'EOF'

# Observability
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-jaeger==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
opentelemetry-instrumentation-requests==0.42b0
python-json-logger==2.0.7
prometheus-client==0.19.0
sentry-sdk[fastapi]==1.39.1
EOF

# Установить зависимости
pip install -r requirements.txt
```

### Шаг 2: Настройка конфигурации

```python
# Добавить в ios_core/config.py

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Observability
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    sentry_dsn: Optional[str] = None
    service_name: str = "ios-system"
    environment: str = "production"
    version: str = "1.1.0"
```

### Шаг 3: Интеграция в приложение

```python
# Обновить api/main.py

from ios_core.observability import setup_tracing, setup_logging, setup_metrics
from api.middleware.observability import ObservabilityMiddleware

# Setup observability
setup_logging(log_level="INFO", json_format=True)
setup_tracing("ios-api")
setup_metrics()

# Add middleware
app.add_middleware(ObservabilityMiddleware)

# Add metrics endpoint
from api.routes.metrics import router as metrics_router
app.include_router(metrics_router)

# Sentry integration (optional)
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,
        integrations=[FastApiIntegration()]
    )
```

### Шаг 4: Запуск

```bash
# Сделать скрипт исполняемым
chmod +x scripts/setup_observability.sh

# Запустить установку
./scripts/setup_observability.sh

# Проверить статус
docker-compose -f docker-compose.observability.yml ps

# Все сервисы должны быть в состоянии "Up"
```

### Шаг 5: Проверка

```bash
# 1. Jaeger UI
open http://localhost:16686
# Выбрать сервис "ios-api" и искать traces

# 2. Kibana
open http://localhost:5601
# Перейти в Discover, выбрать index pattern "ios-logs-*"

# 3. Metrics
curl http://localhost:8000/metrics
# Должны увидеть Prometheus metrics

# 4. Sentry
open http://localhost:9000
# Создать аккаунт и проект

# 5. Тестовые запросы
curl -X POST "http://localhost:8000/api/auth/token" \
  -d "username=admin&password=admin"

# Проверить traces в Jaeger
# Проверить logs в Kibana
```

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

После выполнения Day 113-114:

✅ **Jaeger**
- Distributed tracing работает
- Traces видны в UI
- Все HTTP requests трейсятся
- Database queries видны

✅ **ELK Stack**
- Logs централизованы
- JSON-формат
- Поиск работает
- Dashboards созданы

✅ **Prometheus + Grafana**
- Metrics собираются
- Dashboards обновлены
- Alerts настроены

✅ **Sentry**
- Error tracking работает
- Exceptions captured
- Source maps загружены

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

**Day 115-116:** Elasticsearch Migration
**Day 117-118:** Security Enhancement (Audit Logging + 2FA)

**Готовы продолжить?**