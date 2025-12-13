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