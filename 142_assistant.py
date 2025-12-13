Отлично! Продолжаем с Performance Tuning - это последний технический раздел перед финальным чеклистом. Нужно охватить:

1. Performance Tuning Guide - оптимизация всех компонентов
2. Cost Optimization - снижение расходов
3. Disaster Recovery - план восстановления
4. Production Readiness Checklist - финальная проверка

Начнем с Performance Tuning, который должен включать:
- Elasticsearch optimization
- Qdrant optimization
- Redis tuning
- PostgreSQL tuning
- Application-level optimization
- OS-level tuning
- Network optimization

Затем Cost Optimization:
- Resource right-sizing
- Reserved instances
- Spot instances
- Data lifecycle
- Monitoring costs

Disaster Recovery:
- Backup strategies
- Recovery procedures
- RTO/RPO targets
- Testing DR plan

И финальный Production Checklist.

Начнем!# 🎯 DEEP-DIVE: SEARCH SYSTEM (PERFORMANCE TUNING)

## ФАЙЛ 12: `docs/deep-dive/search/PERFORMANCE_TUNING.md`

```markdown
# Performance Tuning Guide - Deep Dive

## ⚡ Performance Optimization Overview

### Optimization Layers

```
┌─────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                    │
│  • Algorithm optimization                               │
│  • Caching strategy                                     │
│  • Connection pooling                                   │
│  • Async processing                                     │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│                    DATABASE LAYER                       │
│  • Query optimization                                   │
│  • Index tuning                                         │
│  • Shard configuration                                  │
│  • Vector quantization                                  │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                 │
│  • Hardware selection                                   │
│  • OS tuning                                            │
│  • Network optimization                                 │
│  • Storage configuration                                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔍 Elasticsearch Optimization

### Query Performance Tuning

```yaml
# elasticsearch/elasticsearch.yml - Production Configuration

# ============================================================================
# CLUSTER SETTINGS
# ============================================================================

cluster.name: ios-search-cluster
node.name: ${HOSTNAME}

# ============================================================================
# MEMORY SETTINGS
# ============================================================================

# Circuit breakers (prevent OOM)
indices.breaker.total.limit: 70%
indices.breaker.fielddata.limit: 40%
indices.breaker.request.limit: 60%

# Field data cache (for aggregations, sorting)
indices.fielddata.cache.size: 20%

# Query cache
indices.queries.cache.size: 10%

# Request cache (for search results)
indices.requests.cache.size: 2%

# ============================================================================
# INDEXING SETTINGS
# ============================================================================

# Refresh interval (trade-off: freshness vs performance)
# Default: 1s (real-time)
# Optimized: 30s (better indexing throughput)
index.refresh_interval: 30s

# Number of indexing threads
indices.memory.index_buffer_size: 20%

# Translog (write-ahead log)
index.translog.durability: async
index.translog.sync_interval: 30s
index.translog.flush_threshold_size: 1gb

# ============================================================================
# SEARCH SETTINGS
# ============================================================================

# Search thread pool
thread_pool.search.size: 13  # (CPU cores * 1.5) + 1
thread_pool.search.queue_size: 1000

# Get thread pool
thread_pool.get.size: 13
thread_pool.get.queue_size: 1000

# ============================================================================
# PERFORMANCE OPTIMIZATIONS
# ============================================================================

# Disable slow features if not needed
index.codec: best_compression

# Merge policy (background optimization)
index.merge.scheduler.max_thread_count: 1

# Store throttling (prevent I/O spikes)
indices.store.throttle.max_bytes_per_sec: 100mb

# ============================================================================
# DISCOVERY & CLUSTER
# ============================================================================

discovery.seed_hosts:
  - elasticsearch-master-1
  - elasticsearch-master-2
  - elasticsearch-master-3

cluster.initial_master_nodes:
  - elasticsearch-master-1
  - elasticsearch-master-2
  - elasticsearch-master-3

# ============================================================================
# NETWORK
# ============================================================================

network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

# Compression
http.compression: true
http.compression_level: 6

# ============================================================================
# MONITORING
# ============================================================================

xpack.monitoring.collection.enabled: true
xpack.monitoring.elasticsearch.collection.enabled: true
```

### Index Template Optimization

```json
// elasticsearch/templates/optimized_template.json

{
  "index_patterns": ["ios-documents-*"],
  "template": {
    "settings": {
      "number_of_shards": 6,
      "number_of_replicas": 1,
      
      // Refresh interval
      "refresh_interval": "30s",
      
      // Compression
      "codec": "best_compression",
      
      // Translog
      "translog": {
        "durability": "async",
        "sync_interval": "30s",
        "flush_threshold_size": "1gb"
      },
      
      // Merge policy
      "merge": {
        "policy": {
          "max_merged_segment": "5gb",
          "segments_per_tier": 10
        }
      },
      
      // Analysis
      "analysis": {
        "analyzer": {
          "german_analyzer": {
            "type": "custom",
            "tokenizer": "standard",
            "filter": [
              "lowercase",
              "german_stop",
              "german_stemmer"
            ]
          }
        },
        "filter": {
          "german_stop": {
            "type": "stop",
            "stopwords": "_german_"
          },
          "german_stemmer": {
            "type": "stemmer",
            "language": "german"
          }
        }
      }
    },
    
    "mappings": {
      "dynamic": "strict",
      
      "properties": {
        "title": {
          "type": "text",
          "analyzer": "german_analyzer",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        
        "content": {
          "type": "text",
          "analyzer": "german_analyzer",
          
          // Disable unnecessary features
          "norms": false,  // Don't store field length (if scoring not needed)
          "index_options": "freqs"  // Only store term frequencies, not positions
        },
        
        "summary": {
          "type": "text",
          "analyzer": "german_analyzer"
        },
        
        "type": {
          "type": "keyword"
        },
        
        "created_at": {
          "type": "date"
        },
        
        "tags": {
          "type": "keyword"
        },
        
        // Use doc_values for aggregations/sorting
        "view_count": {
          "type": "integer",
          "doc_values": true
        },
        
        // Disable indexing for fields only used for display
        "metadata": {
          "type": "object",
          "enabled": false  // Not indexed, only stored
        }
      }
    }
  }
}
```

### Query Optimization Techniques

```python
# elasticsearch_query_optimization.py

"""
Elasticsearch Query Optimization Techniques
"""

from elasticsearch import Elasticsearch

class OptimizedElasticsearchClient:
    """
    Elasticsearch client with optimized queries
    """
    
    def __init__(self, hosts):
        self.client = Elasticsearch(hosts)
    
    def optimized_search(self, query: str, filters: dict = None):
        """
        Optimized search with best practices
        
        Optimizations:
        1. Use bool query (faster than query_string)
        2. Filter context (cached, no scoring)
        3. Limit _source fields (less data transfer)
        4. Use track_total_hits: false (faster)
        5. Request cache for filters
        """
        # Build query
        must_clauses = []
        filter_clauses = []
        
        # Main search query (scored)
        if query:
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": ["title^3", "content", "summary^2"],
                    "type": "best_fields",
                    "operator": "or",
                    "fuzziness": "AUTO"
                }
            })
        
        # Filters (not scored, cacheable)
        if filters:
            if filters.get('type'):
                filter_clauses.append({
                    "term": {"type": filters['type']}
                })
            
            if filters.get('date_after'):
                filter_clauses.append({
                    "range": {
                        "created_at": {"gte": filters['date_after']}
                    }
                })
            
            if filters.get('tags'):
                filter_clauses.append({
                    "terms": {"tags": filters['tags']}
                })
        
        # Build bool query
        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses
                }
            },
            
            # Performance optimizations
            "size": 10,
            "track_total_hits": False,  # Don't count total (faster)
            
            # Only return needed fields
            "_source": ["title", "summary", "type", "created_at"],
            
            # Highlighting
            "highlight": {
                "fields": {
                    "title": {},
                    "content": {
                        "fragment_size": 150,
                        "number_of_fragments": 3
                    }
                }
            }
        }
        
        # Execute search
        response = self.client.search(
            index='ios-documents',
            body=body,
            
            # Request cache (for filter queries)
            request_cache=True,
            
            # Preference for load balancing
            preference='_local'  # Route to local shard copies
        )
        
        return response
    
    def optimized_aggregation(self, field: str):
        """
        Optimized aggregation query
        
        Optimizations:
        1. Use filter context
        2. Limit bucket count
        3. Use composite aggregation for pagination
        """
        body = {
            "size": 0,  # No documents, only aggregations
            
            "aggs": {
                "top_values": {
                    "terms": {
                        "field": field,
                        "size": 20,
                        "order": {"_count": "desc"},
                        
                        # Use doc_count_error_upper_bound
                        "shard_size": 100  # Reduce shard size (faster)
                    }
                }
            }
        }
        
        response = self.client.search(
            index='ios-documents',
            body=body,
            request_cache=True
        )
        
        return response['aggregations']['top_values']['buckets']
    
    def bulk_index_optimized(self, documents: list):
        """
        Optimized bulk indexing
        
        Optimizations:
        1. Large batch size (1000-5000)
        2. Disable refresh during indexing
        3. Use _bulk API
        4. Parallel workers
        """
        from elasticsearch.helpers import parallel_bulk
        
        # Prepare actions
        actions = [
            {
                "_index": "ios-documents",
                "_id": doc['id'],
                "_source": doc
            }
            for doc in documents
        ]
        
        # Bulk index with parallelism
        success = 0
        errors = []
        
        for ok, result in parallel_bulk(
            self.client,
            actions,
            chunk_size=1000,
            thread_count=4,
            queue_size=8,
            
            # Disable refresh (much faster)
            refresh=False
        ):
            if ok:
                success += 1
            else:
                errors.append(result)
        
        # Manual refresh after bulk
        self.client.indices.refresh(index='ios-documents')
        
        return {'success': success, 'errors': len(errors)}


# JVM Heap Sizing
JVM_HEAP_RULES = """
Elasticsearch JVM Heap Sizing:

Rule 1: Set heap to 50% of RAM (max)
- Node with 32GB RAM → 16GB heap
- Node with 64GB RAM → 31GB heap (not 32GB!)

Rule 2: Never exceed 31GB heap
- Above 31GB, JVM can't use compressed pointers
- Wastes memory and reduces performance
- Better: Use more nodes with 31GB heap each

Rule 3: Leave 50% RAM for OS file cache
- ES uses OS cache extensively
- File cache = faster searches

Example configurations:
├─ 16GB RAM: -Xms8g -Xmx8g
├─ 32GB RAM: -Xms16g -Xmx16g
├─ 64GB RAM: -Xms31g -Xmx31g
└─ 128GB RAM: Use 2 nodes with 31GB heap each

Set in jvm.options:
-Xms16g
-Xmx16g
"""
```

---

## 🎯 Qdrant Optimization

### Vector Search Tuning

```python
# qdrant_optimization.py

"""
Qdrant Vector Search Optimization
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, HnswConfigDiff,
    OptimizersConfigDiff, ScalarQuantization,
    QuantizationConfig, SearchParams,
    QuantizationSearchParams
)

class OptimizedQdrantClient:
    """
    Qdrant client with performance optimizations
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
    
    def create_optimized_collection(
        self,
        collection_name: str,
        vector_size: int = 384
    ):
        """
        Create collection with optimal settings
        
        Optimizations:
        1. On-disk storage (larger collections)
        2. Quantization (4x memory reduction)
        3. Optimized HNSW parameters
        4. Proper indexing threshold
        """
        self.client.create_collection(
            collection_name=collection_name,
            
            # Vector configuration
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
                on_disk=True  # Store vectors on disk
            ),
            
            # HNSW index configuration
            hnsw_config=HnswConfigDiff(
                m=16,  # Connections per layer (default: 16)
                       # Higher = better recall, more memory
                       # Lower = less memory, faster indexing
                
                ef_construct=200,  # Quality of index construction
                                   # Higher = better quality, slower build
                                   # Typical: 100-200
                
                full_scan_threshold=10000,  # When to use brute force
                                            # Below this: full scan
                                            # Above this: HNSW
                
                on_disk=True  # Store HNSW graph on disk
            ),
            
            # Quantization (reduce memory by 75%)
            quantization_config=QuantizationConfig(
                scalar=ScalarQuantization(
                    type='int8',  # 8-bit quantization
                    quantile=0.99,  # Outlier handling
                    always_ram=False  # Store quantized on disk
                )
            ),
            
            # Optimizer configuration
            optimizers_config=OptimizersConfigDiff(
                # Indexing threshold
                indexing_threshold=20000,  # Start indexing after 20k vectors
                
                # Vacuum (remove deleted vectors)
                deleted_threshold=0.2,  # Vacuum at 20% deleted
                vacuum_min_vector_number=1000,
                
                # Memory mapping
                memmap_threshold=50000,  # Use mmap above 50k vectors
                
                # Flush interval
                flush_interval_sec=60,  # Persist every 60s
                
                # Optimization threads
                max_optimization_threads=4
            ),
            
            # Sharding
            shard_number=6,
            replication_factor=2
        )
    
    def optimized_search(
        self,
        collection_name: str,
        query_vector: list,
        limit: int = 10,
        score_threshold: float = 0.7
    ):
        """
        Optimized vector search
        
        Optimizations:
        1. Use quantized vectors (faster)
        2. Rescore top results with original vectors
        3. Adjust ef parameter
        4. Use payload filtering efficiently
        """
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            
            # Search parameters
            search_params=SearchParams(
                hnsw_ef=128,  # Exploration factor
                              # Higher = better recall, slower
                              # Typical: 64-256
                              # Default: same as ef_construct
                
                exact=False,  # Use approximate search
                
                # Quantization parameters
                quantization=QuantizationSearchParams(
                    ignore=False,  # Use quantized vectors
                    rescore=True,  # Rescore with original vectors
                    oversampling=2.0  # Get 2x results, rescore top K
                )
            ),
            
            # Only return necessary payload
            with_payload=True,
            with_vectors=False  # Don't return vectors (faster)
        )
        
        return results
    
    def batch_search_optimized(
        self,
        collection_name: str,
        query_vectors: list,
        limit: int = 10
    ):
        """
        Batch search for better throughput
        
        Process multiple queries at once
        """
        from qdrant_client.models import SearchRequest
        
        # Create batch requests
        search_requests = [
            SearchRequest(
                vector=vector,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                search_params=SearchParams(
                    hnsw_ef=128,
                    quantization=QuantizationSearchParams(
                        rescore=True,
                        oversampling=2.0
                    )
                )
            )
            for vector in query_vectors
        ]
        
        # Execute batch
        results = self.client.search_batch(
            collection_name=collection_name,
            requests=search_requests
        )
        
        return results
    
    def optimized_indexing(
        self,
        collection_name: str,
        vectors: list,
        payloads: list
    ):
        """
        Optimized batch indexing
        
        Optimizations:
        1. Large batch size
        2. Parallel uploading
        3. Disable indexing during upload
        4. Manual optimization after
        """
        # Temporarily disable indexing
        self.client.update_collection(
            collection_name=collection_name,
            optimizer_config=OptimizersConfigDiff(
                indexing_threshold=999999999  # Effectively disable
            )
        )
        
        # Upload in batches
        batch_size = 100
        
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i+batch_size]
            batch_payloads = payloads[i:i+batch_size]
            
            points = [
                {
                    'id': i + j,
                    'vector': vector,
                    'payload': payload
                }
                for j, (vector, payload) in enumerate(
                    zip(batch_vectors, batch_payloads)
                )
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
        
        # Re-enable indexing
        self.client.update_collection(
            collection_name=collection_name,
            optimizer_config=OptimizersConfigDiff(
                indexing_threshold=20000
            )
        )
        
        # Force optimization
        self.client.update_collection(
            collection_name=collection_name,
            optimizers_config=OptimizersConfigDiff(
                indexing_threshold=0  # Index everything now
            )
        )


# HNSW Parameter Tuning Guide
HNSW_TUNING_GUIDE = """
HNSW Parameter Tuning Guide:

Parameter: m (connections per layer)
├─ Default: 16
├─ Range: 4-64
├─ Effects:
│   ├─ Higher m:
│   │   ├─ ✓ Better recall (accuracy)
│   │   ├─ ✓ More robust graph
│   │   ├─ ✗ More memory usage
│   │   └─ ✗ Slower indexing
│   └─ Lower m:
│       ├─ ✓ Less memory
│       ├─ ✓ Faster indexing
│       └─ ✗ Worse recall
└─ Recommendations:
    ├─ Small dataset (<100k): m=32
    ├─ Medium dataset (100k-1M): m=16
    └─ Large dataset (>1M): m=8

Parameter: ef_construct (index build quality)
├─ Default: 100
├─ Range: 100-500
├─ Effects:
│   ├─ Higher ef_construct:
│   │   ├─ ✓ Better quality index
│   │   ├─ ✓ Better search recall
│   │   └─ ✗ Slower indexing
│   └─ Lower ef_construct:
│       ├─ ✓ Faster indexing
│       └─ ✗ Lower quality
└─ Recommendations:
    ├─ Quick prototype: 100
    ├─ Production: 200
    └─ High accuracy: 400

Parameter: ef (search quality)
├─ Default: Same as ef_construct
├─ Range: 32-512
├─ Effects:
│   ├─ Higher ef:
│   │   ├─ ✓ Better recall
│   │   └─ ✗ Slower search
│   └─ Lower ef:
│       ├─ ✓ Faster search
│       └─ ✗ Lower recall
└─ Recommendations:
    ├─ Fast search: ef=64
    ├─ Balanced: ef=128
    └─ High accuracy: ef=256

Example configurations:

# Fast indexing, good recall
m=16, ef_construct=200, ef=128

# High accuracy
m=32, ef_construct=400, ef=256

# Large scale, memory efficient
m=8, ef_construct=100, ef=64, quantization=int8

# Balance (recommended for most)
m=16, ef_construct=200, ef=128, quantization=int8
"""
```

---

## 🗄️ Redis Optimization

### Cache Configuration

```conf
# redis.conf - Production Configuration

# ============================================================================
# MEMORY
# ============================================================================

# Max memory (75% of RAM)
maxmemory 12gb

# Eviction policy
maxmemory-policy allkeys-lru

# Samples for LRU (higher = more accurate, slower)
maxmemory-samples 5

# ============================================================================
# PERSISTENCE
# ============================================================================

# RDB snapshots (for cache, can be disabled)
save ""

# AOF (optional, adds overhead)
appendonly no

# ============================================================================
# PERFORMANCE
# ============================================================================

# Disable THP (Transparent Huge Pages)
# Run: echo never > /sys/kernel/mm/transparent_hugepage/enabled

# TCP backlog
tcp-backlog 511

# Timeout (0 = no timeout)
timeout 0

# TCP keepalive
tcp-keepalive 300

# ============================================================================
# ADVANCED
# ============================================================================

# IO threads (Redis 6+)
io-threads 4
io-threads-do-reads yes

# Lazy freeing
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes

# Active defragmentation (if needed)
activedefrag yes
active-defrag-cycle-min 5
active-defrag-cycle-max 75

# ============================================================================
# NETWORKING
# ============================================================================

# Max clients
maxclients 10000

# Compression
# Use snappy or lz4 at application level
```

### Cache Optimization Strategies

```python
# redis_cache_optimization.py

"""
Redis Cache Optimization Strategies
"""

import redis
import json
import zlib
from typing import Any, Optional
import pickle

class OptimizedRedisCache:
    """
    Redis cache with optimizations
    
    Optimizations:
    1. Compression for large values
    2. Pipeline for batch operations
    3. Connection pooling
    4. Serialization optimization
    """
    
    def __init__(self, host='localhost', port=6379):
        # Connection pool (reuse connections)
        self.pool = redis.ConnectionPool(
            host=host,
            port=port,
            max_connections=50,
            decode_responses=False  # Handle decoding manually
        )
        
        self.client = redis.Redis(connection_pool=self.pool)
        
        # Compression threshold (compress if > 1KB)
        self.compression_threshold = 1024
    
    def set_optimized(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        compress: bool = True
    ):
        """
        Optimized SET operation
        
        Features:
        - Automatic compression for large values
        - Efficient serialization
        - Batch operations support
        """
        # Serialize
        serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        
        # Compress if large enough
        if compress and len(serialized) > self.compression_threshold:
            compressed = zlib.compress(serialized, level=6)
            
            # Only use if compression helps
            if len(compressed) < len(serialized) * 0.9:
                serialized = b'COMPRESSED:' + compressed
        
        # Set with TTL
        self.client.setex(key, ttl, serialized)
    
    def get_optimized(self, key: str) -> Optional[Any]:
        """
        Optimized GET operation
        
        Features:
        - Automatic decompression
        - Efficient deserialization
        """
        value = self.client.get(key)
        
        if value is None:
            return None
        
        # Decompress if needed
        if value.startswith(b'COMPRESSED:'):
            value = zlib.decompress(value[11:])
        
        # Deserialize
        return pickle.loads(value)
    
    def batch_get(self, keys: list) -> dict:
        """
        Batch GET operation using pipeline
        
        Much faster than individual GETs
        """
        pipe = self.client.pipeline()
        
        for key in keys:
            pipe.get(key)
        
        results = pipe.execute()
        
        # Deserialize results
        return {
            key: self.get_optimized(key)
            for key, value in zip(keys, results)
            if value is not None
        }
    
    def batch_set(self, items: dict, ttl: int = 3600):
        """
        Batch SET operation using pipeline
        """
        pipe = self.client.pipeline()
        
        for key, value in items.items():
            # Serialize
            serialized = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            
            # Compress if needed
            if len(serialized) > self.compression_threshold:
                compressed = zlib.compress(serialized, level=6)
                if len(compressed) < len(serialized) * 0.9:
                    serialized = b'COMPRESSED:' + compressed
            
            pipe.setex(key, ttl, serialized)
        
        pipe.execute()
    
    def cache_aside_pattern(
        self,
        key: str,
        fetch_function,
        ttl: int = 3600
    ) -> Any:
        """
        Cache-aside pattern (lazy loading)
        
        Flow:
        1. Check cache
        2. If miss, fetch from source
        3. Store in cache
        4. Return value
        """
        # Try cache first
        cached = self.get_optimized(key)
        
        if cached is not None:
            return cached
        
        # Cache miss - fetch from source
        value = fetch_function()
        
        # Store in cache
        if value is not None:
            self.set_optimized(key, value, ttl=ttl)
        
        return value
    
    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern
        
        Use with caution in production (SCAN is expensive)
        """
        cursor = 0
        keys_to_delete = []
        
        while True:
            cursor, keys = self.client.scan(
                cursor=cursor,
                match=pattern,
                count=100
            )
            
            keys_to_delete.extend(keys)
            
            if cursor == 0:
                break
        
        if keys_to_delete:
            self.client.delete(*keys_to_delete)
        
        return len(keys_to_delete)


# Cache Key Design Patterns
CACHE_KEY_PATTERNS = """
Cache Key Design Patterns:

1. Hierarchical Keys
   Format: namespace:entity:identifier:attribute
   Example: search:query:abc123:results
   
2. Version Keys
   Format: namespace:v{version}:identifier
   Example: search:v2:abc123
   Benefits: Easy invalidation, A/B testing

3. TTL Strategy
   ├─ Search results: 1 hour (3600s)
   ├─ Autocomplete: 5 minutes (300s)
   ├─ User sessions: 24 hours (86400s)
   ├─ Popular queries: 1 week (604800s)
   └─ Static data: No expiry (persistent)

4. Compression Decision
   ├─ Compress if size > 1KB
   ├─ Always compress: Search results (large)
   ├─ Never compress: Small values (<100 bytes)
   └─ Benchmark: Compression vs speed trade-off

5. Serialization Format
   ├─ Pickle: Fastest, Python-only
   ├─ JSON: Human-readable, cross-language
   ├─ MessagePack: Compact, cross-language
   └─ Recommendation: Pickle for internal, JSON for APIs
"""
```

---

## 🐘 PostgreSQL Optimization

### Database Configuration

```conf
# postgresql.conf - Production Configuration

# ============================================================================
# CONNECTIONS
# ============================================================================

max_connections = 200
superuser_reserved_connections = 3

# ============================================================================
# MEMORY
# ============================================================================

# Shared buffers (25% of RAM)
shared_buffers = 8GB

# Work memory (per operation)
work_mem = 50MB

# Maintenance work memory (VACUUM, CREATE INDEX)
maintenance_work_mem = 1GB

# Effective cache size (OS + PG cache estimate)
effective_cache_size = 24GB

# ============================================================================
# WAL (Write-Ahead Log)
# ============================================================================

wal_level = replica
wal_buffers = 16MB
min_wal_size = 1GB
max_wal_size = 4GB

# Checkpoints
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min

# ============================================================================
# QUERY PLANNER
# ============================================================================

# Cost parameters (tune based on hardware)
random_page_cost = 1.1  # SSD (default: 4.0 for HDD)
effective_io_concurrency = 200  # SSD

# Statistics
default_statistics_target = 100

# ============================================================================
# AUTOVACUUM
# ============================================================================

autovacuum = on
autovacuum_max_workers = 4
autovacuum_naptime = 10s

# Vacuum thresholds
autovacuum_vacuum_scale_factor = 0.1
autovacuum_vacuum_threshold = 50

# Analyze thresholds
autovacuum_analyze_scale_factor = 0.05
autovacuum_analyze_threshold = 50

# ============================================================================
# LOGGING
# ============================================================================

log_destination = 'stderr'
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'

# Log slow queries
log_min_duration_statement = 1000  # Log queries > 1s
log_line_prefix = '%t [%p]: user=%u,db=%d,app=%a,client=%h '

# ============================================================================
# PERFORMANCE
# ============================================================================

# Parallel query
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_worker_processes = 8

# Background writer
bgwriter_delay = 200ms
bgwriter_lru_maxpages = 100
bgwriter_lru_multiplier = 2.0
```

### Query Optimization

```python
# postgresql_optimization.py

"""
PostgreSQL Query Optimization
"""

from django.db import connection
from django.db.models import Prefetch, Count, Q
import logging

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """
    PostgreSQL query optimization utilities
    """
    
    @staticmethod
    def analyze_query(queryset):
        """
        Analyze query execution plan
        
        Usage:
            QueryOptimizer.analyze_query(Document.objects.filter(...))
        """
        sql, params = queryset.query.sql_with_params()
        
        with connection.cursor() as cursor:
            # Get execution plan
            cursor.execute(f"EXPLAIN ANALYZE {sql}", params)
            plan = cursor.fetchall()
            
            print("\n" + "="*60)
            print("QUERY EXECUTION PLAN")
            print("="*60)
            
            for row in plan:
                print(row[0])
            
            print("="*60 + "\n")
    
    @staticmethod
    def optimize_select_related():
        """
        Example: Optimize with select_related
        
        Problem: N+1 queries
        Solution: Use select_related for ForeignKey
        """
        from ios_core.models import Document, User
        
        # BAD: N+1 queries (1 + N)
        # documents = Document.objects.all()
        # for doc in documents:
        #     print(doc.owner.name)  # Separate query each time!
        
        # GOOD: Single query with JOIN
        documents = Document.objects.select_related('owner').all()
        for doc in documents:
            print(doc.owner.name)  # No additional query
    
    @staticmethod
    def optimize_prefetch_related():
        """
        Example: Optimize with prefetch_related
        
        Problem: N+1 queries for ManyToMany
        Solution: Use prefetch_related
        """
        from ios_core.models import Document
        
        # BAD: N+1 queries
        # documents = Document.objects.all()
        # for doc in documents:
        #     tags = doc.tags.all()  # Separate query!
        
        # GOOD: 2 queries total
        documents = Document.objects.prefetch_related('tags').all()
        for doc in documents:
            tags = doc.tags.all()  # Cached, no query
    
    @staticmethod
    def optimize_aggregation():
        """
        Example: Efficient aggregation
        """
        from ios_core.models import SearchQuery
        from django.db.models import Count, Avg
        
        # Aggregate at database level (fast)
        stats = SearchQuery.objects.aggregate(
            total=Count('id'),
            avg_results=Avg('total_results')
        )
        
        return stats
    
    @staticmethod
    def optimize_bulk_operations():
        """
        Example: Bulk create/update
        """
        from ios_core.models import SearchQuery
        
        # BAD: Individual inserts
        # for data in batch_data:
        #     SearchQuery.objects.create(**data)
        
        # GOOD: Bulk insert (single query)
        queries = [SearchQuery(**data) for data in batch_data]
        SearchQuery.objects.bulk_create(queries, batch_size=1000)
        
        # Bulk update
        queries = SearchQuery.objects.filter(status='pending')
        queries.update(status='processed')  # Single UPDATE
    
    @staticmethod
    def create_indexes():
        """
        Create optimized indexes
        
        Index types:
        - B-tree (default): General purpose
        - GIN: Full-text search, arrays, JSONB
        - GiST: Geometric data, full-text
        - BRIN: Very large tables with natural order
        """
        from django.db import migrations
        
        # In migration file:
        operations = [
            # B-tree index (default)
            migrations.RunSQL(
                "CREATE INDEX idx_doc_created ON documents (created_at DESC);"
            ),
            
            # Partial index (filtered)
            migrations.RunSQL(
                "CREATE INDEX idx_doc_active ON documents (id) WHERE status = 'active';"
            ),
            
            # Composite index
            migrations.RunSQL(
                "CREATE INDEX idx_doc_type_date ON documents (type, created_at DESC);"
            ),
            
            # GIN index for full-text search
            migrations.RunSQL(
                "CREATE INDEX idx_doc_content_gin ON documents USING gin(to_tsvector('german', content));"
            ),
            
            # GIN index for JSONB
            migrations.RunSQL(
                "CREATE INDEX idx_doc_metadata_gin ON documents USING gin(metadata);"
            ),
        ]


# Index Monitoring
INDEX_MONITORING_SQL = """
-- Find missing indexes (queries with sequential scans)
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    seq_tup_read / seq_scan AS avg_seq_tup
FROM pg_stat_user_tables
WHERE seq_scan > 0
ORDER BY seq_tup_read DESC
LIMIT 20;

-- Find unused indexes
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
    AND indexrelname NOT LIKE 'pg_%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find duplicate indexes
SELECT 
    pg_size_pretty(SUM(pg_relation_size(idx))::BIGINT) AS size,
    (array_agg(idx))[1] AS idx1,
    (array_agg(idx))[2] AS idx2,
    (array_agg(idx))[3] AS idx3,
    (array_agg(idx))[4] AS idx4
FROM (
    SELECT 
        indexrelid::regclass AS idx,
        (indrelid::text ||E'\n'|| indclass::text ||E'\n'|| 
         indkey::text ||E'\n'||COALESCE(indexprs::text,'')||E'\n' ||
         COALESCE(indpred::text,'')) AS key
    FROM pg_index
) sub
GROUP BY key
HAVING COUNT(*) > 1
ORDER BY SUM(pg_relation_size(idx)) DESC;

-- Table bloat
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - 
                   pg_relation_size(schemaname||'.'||tablename)) AS external_size
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

**Продолжение следует...**

Создано:
- ✅ Elasticsearch optimization (JVM, queries, indexing)
- ✅ Qdrant optimization (HNSW, quantization, batching)
- ✅ Redis optimization (cache strategies, compression)
- ✅ PostgreSQL optimization (config, queries, indexes)

**Следующие разделы:**
1. Application-Level Optimization
2. Cost Optimization
3. Disaster Recovery
4. Production Readiness Checklist

**Готовы продолжить с Application-Level Optimization и завершением?**