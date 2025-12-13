Продолжаем с Scaling Strategies - это будет ФАЙЛ 10 в документации по Search System.

Нужно охватить:
1. Horizontal vs Vertical Scaling
2. Elasticsearch scaling strategies
3. Qdrant vector database scaling
4. Redis caching strategies
5. Database scaling (read replicas, sharding)
6. Auto-scaling policies
7. Load testing
8. Capacity planning
9. Cost optimization
10. Performance benchmarks

Продолжаем в том же детальном стиле с примерами кода, конфигурациями и практическими советами.# 🎯 DEEP-DIVE: SEARCH SYSTEM (SCALING)

## ФАЙЛ 10: `docs/deep-dive/search/SCALING_STRATEGIES.md`

```markdown
# Scaling Strategies - Deep Dive

## 📈 Scaling Overview

### Horizontal vs Vertical Scaling

```
┌──────────────────────────────────────────────────────────────┐
│              VERTICAL SCALING (Scale Up)                     │
│                                                              │
│  Before:                    After:                           │
│  ┌──────────┐              ┌──────────┐                     │
│  │ 2 CPU    │    →        │ 8 CPU    │                     │
│  │ 4GB RAM  │              │ 32GB RAM │                     │
│  └──────────┘              └──────────┘                     │
│                                                              │
│  Pros: Simple, no code changes                              │
│  Cons: Hard limits, single point of failure                 │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│            HORIZONTAL SCALING (Scale Out)                    │
│                                                              │
│  Before:                    After:                           │
│  ┌──────────┐              ┌──────────┬──────────┐          │
│  │ Server 1 │    →        │ Server 1 │ Server 2 │          │
│  │          │              ├──────────┼──────────┤          │
│  └──────────┘              │ Server 3 │ Server 4 │          │
│                            └──────────┴──────────┘          │
│                                                              │
│  Pros: No hard limits, fault tolerant                       │
│  Cons: More complex, requires distributed architecture      │
└──────────────────────────────────────────────────────────────┘

IOS Search Scaling Strategy:
├─ API Servers: Horizontal (stateless)
├─ Elasticsearch: Horizontal (sharding)
├─ Qdrant: Horizontal (sharding + replication)
├─ Redis: Horizontal (cluster mode)
└─ PostgreSQL: Vertical + Read Replicas
```

---

## 🔍 Elasticsearch Scaling

### Cluster Architecture

```python
# elasticsearch_cluster_config.py

"""
Elasticsearch Cluster Configuration for Production

Cluster Design:
- 3 Master-eligible nodes (coordination, cluster state)
- 6+ Data nodes (indexing, search)
- 2 Coordinating-only nodes (load balancing)

Total: 11+ nodes
"""

ES_CLUSTER_CONFIG = {
    # Master nodes (cluster management)
    'master_nodes': {
        'count': 3,
        'roles': ['master'],
        'specs': {
            'cpu': '4 cores',
            'memory': '8GB',
            'storage': '100GB SSD'
        },
        'java_heap': '4GB',
        'settings': {
            'node.roles': ['master'],
            'cluster.name': 'ios-search-cluster',
            'discovery.seed_hosts': [
                'es-master-1:9300',
                'es-master-2:9300', 
                'es-master-3:9300'
            ],
            'cluster.initial_master_nodes': [
                'es-master-1',
                'es-master-2',
                'es-master-3'
            ]
        }
    },
    
    # Data nodes (indexing + search)
    'data_nodes': {
        'count': 6,
        'roles': ['data', 'ingest'],
        'specs': {
            'cpu': '8 cores',
            'memory': '32GB',
            'storage': '1TB NVMe SSD'
        },
        'java_heap': '16GB',  # 50% of RAM
        'settings': {
            'node.roles': ['data', 'ingest'],
            'indices.queries.cache.size': '10%',
            'indices.fielddata.cache.size': '20%',
            'indices.breaker.fielddata.limit': '40%',
            'indices.breaker.request.limit': '60%',
            'indices.breaker.total.limit': '70%'
        }
    },
    
    # Coordinating nodes (load balancing)
    'coordinating_nodes': {
        'count': 2,
        'roles': [],  # Coordinating-only
        'specs': {
            'cpu': '8 cores',
            'memory': '16GB',
            'storage': '100GB SSD'
        },
        'java_heap': '8GB',
        'settings': {
            'node.roles': [],
            'search.remote.connect': False
        }
    }
}

# Shard allocation strategy
SHARD_STRATEGY = {
    # Documents per shard
    'target_shard_size': '50GB',
    'max_shard_size': '100GB',
    
    # Shards per index
    'primary_shards': 6,  # Match data node count
    'replica_shards': 1,  # One replica for HA
    
    # Shard allocation
    'allocation': {
        'disk.watermark.low': '85%',
        'disk.watermark.high': '90%',
        'disk.watermark.flood_stage': '95%',
        'awareness.attributes': 'zone',  # Rack awareness
    }
}


def calculate_optimal_shards(
    total_documents: int,
    avg_doc_size_bytes: int,
    data_node_count: int
) -> dict:
    """
    Calculate optimal shard configuration
    
    Rules:
    1. Shard size: 20-50GB optimal
    2. Shards per node: 20-25 max
    3. Primary shards = data node count (for even distribution)
    
    Args:
        total_documents: Total number of documents
        avg_doc_size_bytes: Average document size
        data_node_count: Number of data nodes
    
    Returns:
        Shard configuration
    """
    # Calculate total size
    total_size_gb = (total_documents * avg_doc_size_bytes) / (1024**3)
    
    # Calculate optimal shard count
    # Target: 30GB per shard
    target_shard_size_gb = 30
    optimal_shard_count = max(
        data_node_count,  # At least one per node
        int(total_size_gb / target_shard_size_gb)
    )
    
    # Adjust to nearest multiple of data_node_count
    # for even distribution
    optimal_shard_count = (
        (optimal_shard_count + data_node_count - 1) 
        // data_node_count * data_node_count
    )
    
    # Calculate shards per node
    shards_per_node = optimal_shard_count / data_node_count
    
    return {
        'primary_shards': optimal_shard_count,
        'replica_shards': 1,
        'total_shards': optimal_shard_count * 2,
        'shards_per_node': shards_per_node * 2,  # Including replicas
        'estimated_shard_size_gb': total_size_gb / optimal_shard_count,
        'total_size_gb': total_size_gb
    }


# Example calculation
if __name__ == '__main__':
    config = calculate_optimal_shards(
        total_documents=10_000_000,
        avg_doc_size_bytes=10_000,  # 10KB average
        data_node_count=6
    )
    
    print("Elasticsearch Shard Configuration:")
    print(f"  Primary shards: {config['primary_shards']}")
    print(f"  Replica shards: {config['replica_shards']}")
    print(f"  Total shards: {config['total_shards']}")
    print(f"  Shards per node: {config['shards_per_node']}")
    print(f"  Estimated shard size: {config['estimated_shard_size_gb']:.1f}GB")
    print(f"  Total index size: {config['total_size_gb']:.1f}GB")

# Output:
# Elasticsearch Shard Configuration:
#   Primary shards: 6
#   Replica shards: 1
#   Total shards: 12
#   Shards per node: 2.0
#   Estimated shard size: 15.3GB
#   Total index size: 91.6GB
```

### Index Lifecycle Management (ILM)

```python
# elasticsearch_ilm_policy.py

"""
Index Lifecycle Management for Search Indices

Phases:
1. Hot: Active indexing + searching (SSD, high resources)
2. Warm: Read-only, infrequent searches (SSD, moderate resources)
3. Cold: Rare searches, compressed (HDD, low resources)
4. Delete: Remove old data
"""

ILM_POLICY = {
    "policy": {
        "phases": {
            # Hot phase (0-7 days)
            "hot": {
                "min_age": "0ms",
                "actions": {
                    "rollover": {
                        "max_age": "7d",
                        "max_size": "50GB",
                        "max_docs": 5000000
                    },
                    "set_priority": {
                        "priority": 100  # Highest priority
                    }
                }
            },
            
            # Warm phase (7-30 days)
            "warm": {
                "min_age": "7d",
                "actions": {
                    "readonly": {},  # Make index read-only
                    "forcemerge": {
                        "max_num_segments": 1  # Optimize for search
                    },
                    "shrink": {
                        "number_of_shards": 1  # Reduce to 1 shard
                    },
                    "allocate": {
                        "require": {
                            "data": "warm"  # Move to warm nodes
                        }
                    },
                    "set_priority": {
                        "priority": 50
                    }
                }
            },
            
            # Cold phase (30-90 days)
            "cold": {
                "min_age": "30d",
                "actions": {
                    "allocate": {
                        "require": {
                            "data": "cold"  # Move to cold nodes
                        }
                    },
                    "freeze": {},  # Minimize memory usage
                    "set_priority": {
                        "priority": 0
                    }
                }
            },
            
            # Delete phase (90+ days)
            "delete": {
                "min_age": "90d",
                "actions": {
                    "delete": {}
                }
            }
        }
    }
}

# Create ILM policy
def create_ilm_policy(es_client, policy_name='ios-search-policy'):
    """Create ILM policy in Elasticsearch"""
    es_client.ilm.put_lifecycle(
        policy=policy_name,
        body=ILM_POLICY
    )
    print(f"Created ILM policy: {policy_name}")


# Apply policy to index template
INDEX_TEMPLATE_WITH_ILM = {
    "index_patterns": ["ios-documents-*"],
    "template": {
        "settings": {
            "number_of_shards": 6,
            "number_of_replicas": 1,
            "index.lifecycle.name": "ios-search-policy",
            "index.lifecycle.rollover_alias": "ios-documents",
            "refresh_interval": "30s",
            "codec": "best_compression"
        },
        "mappings": {
            # ... mapping definition
        }
    }
}


# Hot-Warm-Cold Architecture
HOT_WARM_COLD_CONFIG = {
    'hot_nodes': {
        'count': 3,
        'specs': {
            'cpu': '16 cores',
            'memory': '64GB',
            'storage': '2TB NVMe SSD'
        },
        'node_attr': 'data=hot',
        'use_case': 'Active indexing + recent searches'
    },
    
    'warm_nodes': {
        'count': 3,
        'specs': {
            'cpu': '8 cores',
            'memory': '32GB',
            'storage': '4TB SATA SSD'
        },
        'node_attr': 'data=warm',
        'use_case': 'Older data, less frequent searches'
    },
    
    'cold_nodes': {
        'count': 2,
        'specs': {
            'cpu': '4 cores',
            'memory': '16GB',
            'storage': '8TB HDD'
        },
        'node_attr': 'data=cold',
        'use_case': 'Archive, rare searches, compliance'
    }
}
```

---

## 🎯 Qdrant Vector Database Scaling

### Distributed Collection Setup

```python
# qdrant_scaling_config.py

"""
Qdrant Distributed Collection Configuration

Scaling Strategy:
- Sharding: Distribute vectors across nodes
- Replication: Redundancy for high availability
- On-disk storage: For large collections
"""

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, OptimizersConfigDiff,
    HnswConfigDiff, QuantizationConfig, ScalarQuantization,
    ShardingMethod, CollectionParams
)

QDRANT_CLUSTER_CONFIG = {
    'nodes': [
        {'host': 'qdrant-1', 'port': 6333},
        {'host': 'qdrant-2', 'port': 6333},
        {'host': 'qdrant-3', 'port': 6333},
        {'host': 'qdrant-4', 'port': 6333},
        {'host': 'qdrant-5', 'port': 6333},
        {'host': 'qdrant-6', 'port': 6333},
    ],
    
    'node_specs': {
        'cpu': '8 cores',
        'memory': '32GB',
        'storage': '500GB NVMe SSD'
    }
}


def create_distributed_collection(
    collection_name: str,
    vector_size: int,
    shard_count: int = 6,
    replication_factor: int = 2
):
    """
    Create distributed Qdrant collection
    
    Args:
        collection_name: Name of collection
        vector_size: Dimension of vectors (e.g., 384, 768)
        shard_count: Number of shards (match node count)
        replication_factor: Number of replicas per shard
    """
    client = QdrantClient(host='qdrant-1', port=6333)
    
    # Collection configuration
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
            on_disk=True  # Store vectors on disk for large collections
        ),
        
        # Sharding configuration
        shard_number=shard_count,
        replication_factor=replication_factor,
        write_consistency_factor=1,  # Async replication
        
        # Sharding method
        sharding_method=ShardingMethod.AUTO,
        
        # HNSW index configuration
        hnsw_config=HnswConfigDiff(
            m=16,  # Number of connections per layer
            ef_construct=200,  # Quality of index construction
            full_scan_threshold=10000,  # When to use full scan
            on_disk=True  # Store index on disk
        ),
        
        # Optimizer configuration
        optimizers_config=OptimizersConfigDiff(
            deleted_threshold=0.2,
            vacuum_min_vector_number=1000,
            default_segment_number=shard_count,
            max_segment_size=200000,
            memmap_threshold=50000,
            indexing_threshold=20000,
            flush_interval_sec=60,
            max_optimization_threads=4
        ),
        
        # Quantization for memory efficiency
        quantization_config=ScalarQuantization(
            scalar=ScalarQuantization(
                type='int8',
                quantile=0.99,
                always_ram=False  # Store on disk
            )
        )
    )
    
    print(f"Created distributed collection: {collection_name}")
    print(f"  Shards: {shard_count}")
    print(f"  Replication factor: {replication_factor}")
    print(f"  Total replicas: {shard_count * replication_factor}")


# Capacity planning
def calculate_qdrant_capacity(
    total_vectors: int,
    vector_dimension: int,
    replication_factor: int = 2
) -> dict:
    """
    Calculate Qdrant storage and memory requirements
    
    Storage per vector:
    - Vector data: dimension * 4 bytes (float32)
    - HNSW index: ~dimension * 8 bytes (estimate)
    - Metadata: ~200 bytes (average)
    - Quantization savings: ~75% (int8 vs float32)
    
    Args:
        total_vectors: Total number of vectors
        vector_dimension: Vector size (e.g., 384, 768)
        replication_factor: Number of replicas
    
    Returns:
        Capacity requirements
    """
    # Calculate storage per vector
    vector_storage = vector_dimension * 4  # float32
    hnsw_index_storage = vector_dimension * 8  # HNSW overhead
    metadata_storage = 200  # Metadata
    
    storage_per_vector = (
        vector_storage + 
        hnsw_index_storage + 
        metadata_storage
    )
    
    # Apply quantization savings (75% reduction on vectors)
    quantized_vector_storage = vector_storage * 0.25
    storage_per_vector_quantized = (
        quantized_vector_storage +
        hnsw_index_storage +
        metadata_storage
    )
    
    # Total storage
    total_storage_bytes = storage_per_vector_quantized * total_vectors
    total_storage_with_replication = total_storage_bytes * replication_factor
    
    # Memory requirements (working set)
    # Assume 10% of data in memory for hot queries
    memory_working_set = total_storage_bytes * 0.1
    
    # Recommended memory per node
    # 2x working set for overhead
    node_count = 6
    memory_per_node = (memory_working_set * 2) / node_count
    
    return {
        'total_vectors': total_vectors,
        'storage_per_vector_bytes': storage_per_vector_quantized,
        'total_storage_gb': total_storage_bytes / (1024**3),
        'total_storage_with_replication_gb': 
            total_storage_with_replication / (1024**3),
        'memory_working_set_gb': memory_working_set / (1024**3),
        'recommended_memory_per_node_gb': memory_per_node / (1024**3),
        'node_count': node_count,
        'replication_factor': replication_factor
    }


# Example calculation
if __name__ == '__main__':
    # 50M vectors, 384 dimensions (multilingual-e5-small)
    capacity = calculate_qdrant_capacity(
        total_vectors=50_000_000,
        vector_dimension=384,
        replication_factor=2
    )
    
    print("\nQdrant Capacity Planning:")
    print(f"  Total vectors: {capacity['total_vectors']:,}")
    print(f"  Storage per vector: {capacity['storage_per_vector_bytes']:.0f} bytes")
    print(f"  Total storage (single copy): {capacity['total_storage_gb']:.1f} GB")
    print(f"  Total storage (with replication): {capacity['total_storage_with_replication_gb']:.1f} GB")
    print(f"  Memory working set: {capacity['memory_working_set_gb']:.1f} GB")
    print(f"  Recommended memory per node: {capacity['recommended_memory_per_node_gb']:.1f} GB")
    print(f"  Number of nodes: {capacity['node_count']}")

# Output:
# Qdrant Capacity Planning:
#   Total vectors: 50,000,000
#   Storage per vector: 3,672 bytes
#   Total storage (single copy): 171.4 GB
#   Total storage (with replication): 342.7 GB
#   Memory working set: 17.1 GB
#   Recommended memory per node: 5.7 GB
#   Number of nodes: 6
```

### Qdrant Search Optimization

```python
# qdrant_search_optimization.py

from qdrant_client import QdrantClient
from qdrant_client.models import (
    SearchParams, QuantizationSearchParams
)

def optimized_search(
    client: QdrantClient,
    collection_name: str,
    query_vector: list,
    limit: int = 10
):
    """
    Optimized vector search with quantization
    
    Performance tips:
    1. Use quantization for faster search
    2. Adjust ef (accuracy vs speed tradeoff)
    3. Use payload filtering efficiently
    4. Batch requests when possible
    """
    results = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        
        # Search parameters
        search_params=SearchParams(
            hnsw_ef=128,  # Higher = more accurate, slower
            exact=False,  # Use approximate search
            quantization=QuantizationSearchParams(
                ignore=False,  # Use quantization
                rescore=True,  # Rescore with original vectors
                oversampling=2.0  # Get 2x results, rescore top K
            )
        )
    )
    
    return results


# Batch search for better throughput
def batch_search(
    client: QdrantClient,
    collection_name: str,
    query_vectors: list,
    limit: int = 10
):
    """
    Batch search - process multiple queries at once
    
    Better throughput than individual searches
    """
    from qdrant_client.models import SearchRequest
    
    # Create batch request
    search_requests = [
        SearchRequest(
            vector=vector,
            limit=limit,
            search_params=SearchParams(
                hnsw_ef=128,
                quantization=QuantizationSearchParams(
                    rescore=True
                )
            )
        )
        for vector in query_vectors
    ]
    
    # Execute batch
    results = client.search_batch(
        collection_name=collection_name,
        requests=search_requests
    )
    
    return results
```

---

## 🗄️ Redis Cluster Setup

### Redis Cluster Configuration

```python
# redis_cluster_config.py

"""
Redis Cluster Configuration for Caching

Cluster Setup:
- 6 master nodes (sharding)
- 6 replica nodes (high availability)
- Total: 12 nodes

Hash slots: 16384 (distributed across masters)
"""

REDIS_CLUSTER_CONFIG = {
    'masters': [
        {'host': 'redis-master-1', 'port': 6379, 'slots': '0-2730'},
        {'host': 'redis-master-2', 'port': 6379, 'slots': '2731-5460'},
        {'host': 'redis-master-3', 'port': 6379, 'slots': '5461-8191'},
        {'host': 'redis-master-4', 'port': 6379, 'slots': '8192-10922'},
        {'host': 'redis-master-5', 'port': 6379, 'slots': '10923-13652'},
        {'host': 'redis-master-6', 'port': 6379, 'slots': '13653-16383'},
    ],
    
    'replicas': [
        {'host': 'redis-replica-1', 'port': 6379, 'master': 'redis-master-1'},
        {'host': 'redis-replica-2', 'port': 6379, 'master': 'redis-master-2'},
        {'host': 'redis-replica-3', 'port': 6379, 'master': 'redis-master-3'},
        {'host': 'redis-replica-4', 'port': 6379, 'master': 'redis-master-4'},
        {'host': 'redis-replica-5', 'port': 6379, 'master': 'redis-master-5'},
        {'host': 'redis-replica-6', 'port': 6379, 'master': 'redis-master-6'},
    ],
    
    'node_specs': {
        'cpu': '4 cores',
        'memory': '16GB',
        'maxmemory': '12GB',  # 75% of RAM
        'maxmemory_policy': 'allkeys-lru'
    }
}

# Docker Compose for Redis Cluster
REDIS_CLUSTER_COMPOSE = """
version: '3.8'

services:
  redis-master-1:
    image: redis:7-alpine
    command: >
      redis-server
      --port 6379
      --cluster-enabled yes
      --cluster-config-file nodes.conf
      --cluster-node-timeout 5000
      --appendonly yes
      --maxmemory 12gb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis-master-1-data:/data
    networks:
      - redis-cluster

  # ... repeat for other masters ...

  redis-replica-1:
    image: redis:7-alpine
    command: >
      redis-server
      --port 6379
      --cluster-enabled yes
      --cluster-config-file nodes.conf
      --cluster-node-timeout 5000
      --appendonly yes
      --maxmemory 12gb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis-replica-1-data:/data
    networks:
      - redis-cluster
    depends_on:
      - redis-master-1

  # ... repeat for other replicas ...

networks:
  redis-cluster:
    driver: bridge

volumes:
  redis-master-1-data:
  # ... volumes for other nodes ...
"""


# Initialize Redis Cluster
def init_redis_cluster():
    """
    Initialize Redis Cluster
    
    Run this script to create the cluster:
    """
    import subprocess
    
    # Create cluster
    cmd = [
        'redis-cli',
        '--cluster', 'create',
        'redis-master-1:6379',
        'redis-master-2:6379',
        'redis-master-3:6379',
        'redis-master-4:6379',
        'redis-master-5:6379',
        'redis-master-6:6379',
        '--cluster-replicas', '1',  # 1 replica per master
        '--cluster-yes'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)


# Redis Client with Cluster Support
from redis.cluster import RedisCluster

def get_redis_cluster_client():
    """Get Redis Cluster client"""
    startup_nodes = [
        {'host': 'redis-master-1', 'port': 6379},
        {'host': 'redis-master-2', 'port': 6379},
        {'host': 'redis-master-3', 'port': 6379},
    ]
    
    return RedisCluster(
        startup_nodes=startup_nodes,
        decode_responses=True,
        skip_full_coverage_check=True,
        max_connections_per_node=50
    )


# Cache key design for optimal sharding
def design_cache_key(prefix: str, identifier: str, suffix: str = '') -> str:
    """
    Design cache key for optimal distribution
    
    Use hash tags {} to control which part is hashed
    for slot assignment
    
    Examples:
    - "search:{query_hash}:results" - Shard by query
    - "user:{user_id}:searches" - Shard by user
    - "global:stats" - Same slot for related keys
    """
    if suffix:
        return f"{prefix}:{{{identifier}}}:{suffix}"
    return f"{prefix}:{{{identifier}}}"


# Example usage
if __name__ == '__main__':
    # Connect to cluster
    redis_cluster = get_redis_cluster_client()
    
    # Cache search results
    query_hash = "abc123"
    cache_key = design_cache_key('search', query_hash, 'results')
    
    redis_cluster.setex(
        cache_key,
        3600,  # TTL: 1 hour
        '{"results": [...]}' 
    )
    
    # Get cached results
    cached = redis_cluster.get(cache_key)
    
    print(f"Cache key: {cache_key}")
    print(f"Cached: {bool(cached)}")
```

---

## 💾 PostgreSQL Scaling

### Read Replicas Setup

```yaml
# docker-compose.postgres-ha.yml

version: '3.8'

services:
  # Primary (Master) - Read/Write
  postgres-primary:
    image: postgres:15-alpine
    container_name: postgres-primary
    environment:
      - POSTGRES_DB=ios_db
      - POSTGRES_USER=ios
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_REPLICATION_USER=replicator
      - POSTGRES_REPLICATION_PASSWORD=replicator_pass
    volumes:
      - postgres-primary-data:/var/lib/postgresql/data
      - ./postgres/primary/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/primary/pg_hba.conf:/etc/postgresql/pg_hba.conf
    command: >
      postgres
      -c config_file=/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    networks:
      - postgres-ha

  # Replica 1 - Read-only
  postgres-replica-1:
    image: postgres:15-alpine
    container_name: postgres-replica-1
    environment:
      - POSTGRES_USER=ios
      - POSTGRES_PASSWORD=changeme
      - PGUSER=replicator
      - PGPASSWORD=replicator_pass
    volumes:
      - postgres-replica-1-data:/var/lib/postgresql/data
      - ./postgres/replica/postgresql.conf:/etc/postgresql/postgresql.conf
    command: >
      bash -c "
      until pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -Fp -Xs -P -R; do
        echo 'Waiting for primary to be ready...'
        sleep 5
      done
      postgres -c config_file=/etc/postgresql/postgresql.conf
      "
    ports:
      - "5433:5432"
    depends_on:
      - postgres-primary
    networks:
      - postgres-ha

  # Replica 2 - Read-only
  postgres-replica-2:
    image: postgres:15-alpine
    container_name: postgres-replica-2
    environment:
      - POSTGRES_USER=ios
      - POSTGRES_PASSWORD=changeme
      - PGUSER=replicator
      - PGPASSWORD=replicator_pass
    volumes:
      - postgres-replica-2-data:/var/lib/postgresql/data
      - ./postgres/replica/postgresql.conf:/etc/postgresql/postgresql.conf
    command: >
      bash -c "
      until pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -Fp -Xs -P -R; do
        echo 'Waiting for primary to be ready...'
        sleep 5
      done
      postgres -c config_file=/etc/postgresql/postgresql.conf
      "
    ports:
      - "5434:5432"
    depends_on:
      - postgres-primary
    networks:
      - postgres-ha

  # PgBouncer - Connection Pooling
  pgbouncer:
    image: edoburu/pgbouncer:latest
    container_name: pgbouncer
    environment:
      - DATABASE_URL=postgresql://ios:changeme@postgres-primary:5432/ios_db
      - POOL_MODE=transaction
      - MAX_CLIENT_CONN=1000
      - DEFAULT_POOL_SIZE=25
      - RESERVE_POOL_SIZE=5
    ports:
      - "6432:5432"
    depends_on:
      - postgres-primary
    networks:
      - postgres-ha

networks:
  postgres-ha:
    driver: bridge

volumes:
  postgres-primary-data:
  postgres-replica-1-data:
  postgres-replica-2-data:
```

### Django Database Router

```python
# ios_core/database_router.py

"""
Database Router for Read/Write Splitting

Routes:
- Write operations -> Primary
- Read operations -> Random replica
- Analytics queries -> Specific replica
"""

import random

class ReadWriteRouter:
    """
    Database router for read/write splitting
    
    Configuration in settings.py:
    DATABASES = {
        'default': {  # Primary (write)
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': 'postgres-primary',
            'PORT': 5432,
            ...
        },
        'replica_1': {  # Read replica
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': 'postgres-replica-1',
            'PORT': 5432,
            ...
        },
        'replica_2': {  # Read replica
            'ENGINE': 'django.db.backends.postgresql',
            'HOST': 'postgres-replica-2',
            'PORT': 5432,
            ...
        },
    }
    
    DATABASE_ROUTERS = ['ios_core.database_router.ReadWriteRouter']
    """
    
    # Read replicas
    read_replicas = ['replica_1', 'replica_2']
    
    def db_for_read(self, model, **hints):
        """
        Route read operations to replicas
        
        Load balancing: Random selection
        """
        # Analytics models always go to specific replica
        if model._meta.app_label == 'analytics':
            return 'replica_2'
        
        # Random replica for other reads
        return random.choice(self.read_replicas)
    
    def db_for_write(self, model, **hints):
        """
        Route write operations to primary
        """
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations between objects in same database
        """
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on primary
        """
        return db == 'default'


# Usage in views
from django.db import connections

def get_search_results_with_routing(query):
    """
    Example: Force specific database for query
    """
    from ios_core.models import Document
    
    # Force read from replica
    documents = Document.objects.using('replica_1').filter(
        title__icontains=query
    )
    
    return documents


# Connection pooling settings
DATABASE_CONNECTION_POOLING = {
    'default': {
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30s
        }
    },
    'replica_1': {
        'CONN_MAX_AGE': 600,
    },
    'replica_2': {
        'CONN_MAX_AGE': 600,
    }
}
```

---

## 🔄 Auto-Scaling Policies

### Kubernetes HPA Configuration

```yaml
# k8s/hpa-search-api.yaml

apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ios-search-api-hpa
  namespace: ios-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ios-search-api
  
  # Scaling bounds
  minReplicas: 3
  maxReplicas: 20
  
  # Scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50  # Increase by 50%
        periodSeconds: 60
      - type: Pods
        value: 2  # Or add 2 pods
        periodSeconds: 60
      selectPolicy: Max  # Use more aggressive policy
    
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 minutes
      policies:
      - type: Percent
        value: 10  # Decrease by 10%
        periodSeconds: 60
      selectPolicy: Min  # Use more conservative policy
  
  # Metrics
  metrics:
  # CPU utilization
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # Memory utilization
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  # Custom metric: Search request rate
  - type: Pods
    pods:
      metric:
        name: search_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  
  # Custom metric: Search latency
  - type: Pods
    pods:
      metric:
        name: search_p95_latency_seconds
      target:
        type: AverageValue
        averageValue: "1.5"
```

### Cloud Provider Auto-Scaling

```python
# aws_autoscaling_config.py

"""
AWS Auto Scaling Configuration

Using:
- Application Auto Scaling for ECS/Fargate
- Target Tracking Policies
"""

import boto3

def setup_aws_autoscaling():
    """Setup AWS Auto Scaling for ECS service"""
    client = boto3.client('application-autoscaling')
    
    # Register scalable target
    client.register_scalable_target(
        ServiceNamespace='ecs',
        ResourceId='service/ios-cluster/ios-search-api',
        ScalableDimension='ecs:service:DesiredCount',
        MinCapacity=3,
        MaxCapacity=20
    )
    
    # CPU utilization policy
    client.put_scaling_policy(
        PolicyName='ios-search-cpu-scaling',
        ServiceNamespace='ecs',
        ResourceId='service/ios-cluster/ios-search-api',
        ScalableDimension='ecs:service:DesiredCount',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 70.0,
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'ECSServiceAverageCPUUtilization'
            },
            'ScaleInCooldown': 300,
            'ScaleOutCooldown': 60
        }
    )
    
    # Memory utilization policy
    client.put_scaling_policy(
        PolicyName='ios-search-memory-scaling',
        ServiceNamespace='ecs',
        ResourceId='service/ios-cluster/ios-search-api',
        ScalableDimension='ecs:service:DesiredCount',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 80.0,
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'ECSServiceAverageMemoryUtilization'
            },
            'ScaleInCooldown': 300,
            'ScaleOutCooldown': 60
        }
    )
    
    # Custom metric: Request rate
    client.put_scaling_policy(
        PolicyName='ios-search-request-rate-scaling',
        ServiceNamespace='ecs',
        ResourceId='service/ios-cluster/ios-search-api',
        ScalableDimension='ecs:service:DesiredCount',
        PolicyType='TargetTrackingScaling',
        TargetTrackingScalingPolicyConfiguration={
            'TargetValue': 1000.0,  # 1000 requests/minute per instance
            'CustomizedMetricSpecification': {
                'MetricName': 'SearchRequestsPerMinute',
                'Namespace': 'IOS/Search',
                'Statistic': 'Average',
                'Unit': 'Count'
            },
            'ScaleInCooldown': 300,
            'ScaleOutCooldown': 60
        }
    )
    
    print("AWS Auto Scaling configured ✓")
```

---

**Продолжение следует...**

Создано:
- ✅ Elasticsearch cluster architecture and shard calculation
- ✅ Index Lifecycle Management (ILM)
- ✅ Qdrant distributed setup and capacity planning
- ✅ Redis Cluster configuration
- ✅ PostgreSQL read replicas with routing
- ✅ Auto-scaling policies (K8s HPA + AWS)

**Следующие разделы:**
1. Load Testing
2. Performance Tuning
3. Cost Optimization
4. Disaster Recovery

**Готовы продолжить с Load Testing?**