# performance/optimization.py
"""
Performance Optimization для IOS
"""

from functools import lru_cache, wraps
from time import time
import asyncio
from typing import Callable

# ============================================================================
# CACHING STRATEGIES
# ============================================================================

class CacheStrategy:
    """Стратегии кэширования"""
    
    @staticmethod
    def cache_with_ttl(ttl_seconds: int = 300):
        """Декоратор для кэширования с TTL"""
        
        def decorator(func: Callable):
            cache = {}
            cache_times = {}
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Создать ключ кэша
                cache_key = str(args) + str(kwargs)
                
                # Проверить кэш
                if cache_key in cache:
                    if time() - cache_times[cache_key] < ttl_seconds:
                        return cache[cache_key]
                
                # Вычислить значение
                result = await func(*args, **kwargs)
                
                # Сохранить в кэш
                cache[cache_key] = result
                cache_times[cache_key] = time()
                
                return result
            
            return wrapper
        return decorator


# ============================================================================
# DATABASE OPTIMIZATION
# ============================================================================

class DatabaseOptimizer:
    """Оптимизация работы с базой данных"""
    
    @staticmethod
    def batch_insert(items: list, batch_size: int = 1000):
        """Пакетная вставка"""
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            # Вставить батч
            # db.bulk_insert(batch)
    
    @staticmethod
    def use_connection_pooling():
        """Использовать connection pooling"""
        # SQLAlchemy configuration
        engine_config = {
            'pool_size': 20,
            'max_overflow': 40,
            'pool_pre_ping': True,
            'pool_recycle': 3600
        }
        return engine_config
    
    @staticmethod
    def create_indexes():
        """Создать индексы для часто используемых запросов"""
        indexes = [
            "CREATE INDEX idx_documents_domain ON documents(domain_name)",
            "CREATE INDEX idx_documents_type ON documents(document_type)",
            "CREATE INDEX idx_documents_created ON documents(created_at DESC)",
            "CREATE INDEX idx_entities_type ON entities(type)",
            "CREATE INDEX idx_entities_domain ON entities(domain_name)",
            "CREATE INDEX idx_relations_source ON relations(source_id)",
            "CREATE INDEX idx_relations_target ON relations(target_id)",
            "CREATE INDEX idx_search_queries ON search_queries(query, domain_name)",
        ]
        return indexes


# ============================================================================
# QUERY OPTIMIZATION
# ============================================================================

class QueryOptimizer:
    """Оптимизация запросов"""
    
    @staticmethod
    def use_select_related():
        """Использовать eager loading"""
        # SQLAlchemy: query.options(joinedload(Model.relation))
        pass
    
    @staticmethod
    def paginate_large_results(page: int = 1, page_size: int = 50):
        """Пагинация больших результатов"""
        offset = (page - 1) * page_size
        # query.limit(page_size).offset(offset)
        return offset, page_size
    
    @staticmethod
    def use_bulk_operations():
        """Использовать bulk операции"""
        # db.bulk_update_mappings(Model, mappings)
        pass


# ============================================================================
# ASYNC OPTIMIZATION
# ============================================================================

class AsyncOptimizer:
    """Оптимизация асинхронного кода"""
    
    @staticmethod
    async def parallel_execution(tasks: list):
        """Параллельное выполнение задач"""
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    @staticmethod
    async def batch_process(items: list, batch_size: int = 10):
        """Пакетная обработка с ограничением параллелизма"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[process_item(item) for item in batch]
            )
            results.extend(batch_results)
        
        return results


# ============================================================================
# MEMORY OPTIMIZATION
# ============================================================================

class MemoryOptimizer:
    """Оптимизация использования памяти"""
    
    @staticmethod
    def use_generators():
        """Использовать генераторы вместо списков"""
        # Плохо: items = [process(x) for x in large_list]
        # Хорошо: items = (process(x) for x in large_list)
        pass
    
    @staticmethod
    def stream_large_files():
        """Потоковое чтение больших файлов"""
        def read_in_chunks(file_path: str, chunk_size: int = 8192):
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    yield chunk
        
        return read_in_chunks
    
    @staticmethod
    def cleanup_resources():
        """Очистка неиспользуемых ресурсов"""
        import gc
        gc.collect()


# ============================================================================
# MONITORING & PROFILING
# ============================================================================

class PerformanceMonitor:
    """Мониторинг производительности"""
    
    @staticmethod
    def profile_function(func: Callable):
        """Профилирование функции"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time()
            
            result = await func(*args, **kwargs)
            
            duration = time() - start_time
            
            # Логировать если медленно
            if duration > 1.0:  # более 1 секунды
                print(f"SLOW FUNCTION: {func.__name__} took {duration:.2f}s")
            
            return result
        
        return wrapper
    
    @staticmethod
    def track_query_performance(query: str, duration: float):
        """Отслеживание производительности запросов"""
        # Сохранить в базу для анализа
        if duration > 0.5:  # медленный запрос
            print(f"SLOW QUERY: {query[:100]} took {duration:.2f}s")


# ============================================================================
# RECOMMENDATIONS
# ============================================================================

PERFORMANCE_RECOMMENDATIONS = """
# Performance Optimization Recommendations

## Database
1. **Индексы**: Создать индексы для всех foreign keys и часто используемых полей
2. **Connection Pooling**: Использовать размер пула 20-50 соединений
3. **Query Optimization**: Использовать EXPLAIN ANALYZE для анализа медленных запросов
4. **Денормализация**: Рассмотреть денормализацию для часто читаемых данных
5. **Партиционирование**: Партиционировать большие таблицы по дате

## Caching
1. **Redis**: Кэшировать результаты поиска на 5-15 минут
2. **Application Cache**: Использовать in-memory кэш для конфигурации
3. **CDN**: Использовать CDN для статических файлов
4. **Browser Cache**: Настроить правильные Cache-Control заголовки

## API
1. **Pagination**: Всегда использовать пагинацию для списков (max 100 items)
2. **Field Selection**: Позволить клиентам выбирать нужные поля
3. **Compression**: Включить gzip сжатие для ответов
4. **HTTP/2**: Использовать HTTP/2 для мультиплексирования

## Application
1. **Async**: Использовать async/await для I/O операций
2. **Batch Processing**: Обрабатывать данные батчами, не по одному
3. **Resource Limits**: Установить лимиты для CPU и памяти контейнеров
4. **Lazy Loading**: Загружать данные только когда нужно

## Search
1. **Index Optimization**: Оптимизировать Whoosh/Elasticsearch индексы
2. **Result Caching**: Кэшировать результаты популярных запросов
3. **Fuzzy Search**: Использовать fuzzy search с осторожностью (медленно)
4. **Faceted Search**: Кэшировать фасеты на уровне домена

## Knowledge Graph
1. **Graph Algorithms**: Использовать эффективные алгоритмы (BFS вместо DFS)
2. **Subgraph Extraction**: Работать с подграфами, не полным графом
3. **Caching**: Кэшировать результаты сложных запросов
4. **Materialized Views**: Создать материализованные представления для аналитики
"""