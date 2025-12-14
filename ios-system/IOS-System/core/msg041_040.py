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