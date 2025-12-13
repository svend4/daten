Пользователь готов продолжить с Load Testing. Это следующий логический раздел после scaling strategies. Нужно создать подробное руководство по нагрузочному тестированию системы поиска, включая:

1. Load Testing Tools и конфигурацию
2. Test scenarios (разные типы нагрузки)
3. Performance benchmarks
4. Bottleneck identification
5. Stress testing
6. Chaos engineering

Это будет ФАЙЛ 11 в серии Deep-Dive документации.# 🎯 DEEP-DIVE: SEARCH SYSTEM (LOAD TESTING)

## ФАЙЛ 11: `docs/deep-dive/search/LOAD_TESTING.md`

```markdown
# Load Testing & Performance Benchmarks - Deep Dive

## 🎯 Load Testing Strategy

### Testing Pyramid

```
                    ▲ Complexity
                    │
        ┌───────────────────────┐
        │   Chaos Engineering   │  ← Rare
        │  (Production-like)    │
        └───────────────────────┘
               ┌─────────────────────────┐
               │    Stress Testing       │  ← Occasional
               │  (Breaking points)      │
               └─────────────────────────┘
                    ┌──────────────────────────┐
                    │   Load Testing           │  ← Regular
                    │ (Expected traffic)       │
                    └──────────────────────────┘
                         ┌─────────────────────────────┐
                         │  Performance Testing        │  ← Continuous
                         │ (Individual components)     │
                         └─────────────────────────────┘

Testing Frequency:
├─ Performance: Every commit (CI/CD)
├─ Load: Weekly / Before releases
├─ Stress: Monthly / Major releases
└─ Chaos: Quarterly / Critical updates
```

---

## 🔧 Load Testing Tools

### Locust Configuration

```python
# locustfile.py

"""
Locust Load Testing for IOS Search System

Simulates realistic user behavior:
- Search queries
- Autocomplete requests
- Result clicks
- Analytics tracking

Usage:
    locust -f locustfile.py --host=http://localhost --users=1000 --spawn-rate=10
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import random
import json
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# Test Data
# ============================================================================

# Realistic German search queries (from analytics)
SEARCH_QUERIES = [
    "persönliches budget",
    "personal budget beantragen",
    "budget für persönliche assistenz",
    "hilfe bei behinderung",
    "pflegegeld antrag",
    "sozialhilfe leistungen",
    "eingliederungshilfe",
    "teilhabegesetz",
    "rehabilitation",
    "werkstatt für behinderte menschen",
    "barrierefreiheit",
    "schwerbehindertenausweis",
    "grad der behinderung",
    "persönliche assistenz kosten",
    "ambulant betreutes wohnen",
]

# Autocomplete prefixes
AUTOCOMPLETE_PREFIXES = [
    "per", "pers", "perso", "person",
    "bud", "budg", "budget",
    "hilf", "hilfe",
    "pfle", "pfleg", "pflege",
]

# Document IDs for click simulation
DOCUMENT_IDS = list(range(1, 1001))


# ============================================================================
# User Behavior Classes
# ============================================================================

class SearchUser(HttpUser):
    """
    Simulates typical search user behavior
    
    Behavior patterns:
    1. Enter search query (or use autocomplete)
    2. View results
    3. Maybe click on result
    4. Maybe refine search
    """
    
    # Wait time between tasks (human-like behavior)
    wait_time = between(2, 10)
    
    # User attributes
    user_id = None
    session_id = None
    last_query = None
    last_query_id = None
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = random.randint(1, 10000)
        self.session_id = f"session_{int(time.time())}_{self.user_id}"
        logger.info(f"User {self.user_id} started session {self.session_id}")
    
    @task(10)
    def search(self):
        """
        Execute search query
        
        Weight: 10 (most common action)
        """
        query = random.choice(SEARCH_QUERIES)
        
        # Add variation
        if random.random() < 0.3:
            # 30% of queries are slight variations
            query = query + " " + random.choice(["2024", "antrag", "formular"])
        
        start_time = time.time()
        
        with self.client.post(
            "/api/search/",
            json={
                "query": query,
                "page": 1,
                "page_size": 10
            },
            catch_response=True,
            name="search"
        ) as response:
            elapsed_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.last_query = query
                self.last_query_id = data.get('query_id')
                results_count = len(data.get('results', []))
                
                response.success()
                
                logger.debug(
                    f"Search: '{query}' -> {results_count} results "
                    f"({elapsed_ms:.0f}ms)"
                )
                
                # Maybe click on result
                if results_count > 0 and random.random() < 0.4:
                    # 40% of searches result in click
                    self.click_result(data['results'])
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def autocomplete(self):
        """
        Use autocomplete
        
        Weight: 5 (less common than full search)
        """
        prefix = random.choice(AUTOCOMPLETE_PREFIXES)
        
        with self.client.get(
            f"/api/search/autocomplete?q={prefix}&limit=10",
            catch_response=True,
            name="autocomplete"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                suggestions_count = len(data.get('suggestions', []))
                response.success()
                
                logger.debug(
                    f"Autocomplete: '{prefix}' -> {suggestions_count} suggestions"
                )
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def paginate_results(self):
        """
        Navigate to page 2 of results
        
        Weight: 3 (some users browse multiple pages)
        """
        if not self.last_query:
            return
        
        with self.client.post(
            "/api/search/",
            json={
                "query": self.last_query,
                "page": 2,
                "page_size": 10
            },
            catch_response=True,
            name="search_page_2"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    def click_result(self, results):
        """
        Click on search result
        
        Simulates user clicking on result from search page
        """
        if not results or not self.last_query_id:
            return
        
        # Click on one of top 5 results (most common)
        result = random.choice(results[:5])
        
        # Simulate time to click (1-5 seconds)
        time_to_click_ms = random.randint(1000, 5000)
        
        with self.client.post(
            "/api/search/track_click/",
            json={
                "query_id": self.last_query_id,
                "document_id": result['document_id'],
                "document_title": result['title'],
                "rank": result['rank'],
                "page": 1,
                "scores": {
                    "final": result['score']
                },
                "time_to_click_ms": time_to_click_ms
            },
            catch_response=True,
            name="track_click"
        ) as response:
            if response.status_code == 200:
                response.success()
                logger.debug(
                    f"Click tracked: doc_id={result['document_id']}, "
                    f"rank={result['rank']}"
                )
            else:
                response.failure(f"Status code: {response.status_code}")


class PowerUser(HttpUser):
    """
    Simulates power user behavior
    
    Characteristics:
    - More searches per session
    - Uses filters
    - More pagination
    - Faster interactions
    """
    
    wait_time = between(1, 3)  # Faster than regular users
    
    user_id = None
    session_id = None
    
    def on_start(self):
        self.user_id = random.randint(10000, 20000)
        self.session_id = f"power_session_{int(time.time())}_{self.user_id}"
    
    @task(10)
    def filtered_search(self):
        """Search with filters (power user behavior)"""
        query = random.choice(SEARCH_QUERIES)
        
        filters = {}
        
        # Add random filters
        if random.random() < 0.5:
            filters['type'] = random.choice(['legal_document', 'guide', 'form'])
        
        if random.random() < 0.3:
            filters['date_after'] = '2024-01-01'
        
        with self.client.post(
            "/api/search/",
            json={
                "query": query,
                "page": 1,
                "page_size": 20,  # Power users see more results
                "filters": filters
            },
            catch_response=True,
            name="filtered_search"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(5)
    def batch_autocomplete(self):
        """Multiple autocomplete requests quickly"""
        prefix_base = random.choice(["per", "bud", "hilf"])
        
        for i in range(len(prefix_base)):
            prefix = prefix_base[:i+2]
            
            self.client.get(
                f"/api/search/autocomplete?q={prefix}&limit=10",
                name="autocomplete_typing"
            )
            
            time.sleep(0.1)  # 100ms between keystrokes


# ============================================================================
# Load Testing Scenarios
# ============================================================================

class NormalLoad(HttpUser):
    """
    Normal business hours load
    
    User distribution:
    - 80% SearchUser (regular users)
    - 20% PowerUser (power users)
    """
    tasks = [SearchUser, PowerUser]
    weights = [8, 2]


class PeakLoad(HttpUser):
    """
    Peak load (e.g., Monday mornings)
    
    3x normal load
    """
    tasks = [SearchUser, PowerUser]
    weights = [8, 2]
    wait_time = between(1, 5)  # Faster interactions during peak


# ============================================================================
# Events & Reporting
# ============================================================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test start"""
    print("\n" + "="*60)
    print("LOAD TEST STARTED")
    print("="*60)
    print(f"Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("="*60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate test report"""
    print("\n" + "="*60)
    print("LOAD TEST COMPLETED")
    print("="*60)
    
    stats = environment.stats
    
    # Overall statistics
    print(f"\nTotal requests: {stats.total.num_requests}")
    print(f"Failed requests: {stats.total.num_failures}")
    print(f"Failure rate: {stats.total.fail_ratio:.2%}")
    print(f"Average response time: {stats.total.avg_response_time:.0f}ms")
    print(f"P50: {stats.total.get_response_time_percentile(0.5):.0f}ms")
    print(f"P95: {stats.total.get_response_time_percentile(0.95):.0f}ms")
    print(f"P99: {stats.total.get_response_time_percentile(0.99):.0f}ms")
    print(f"RPS: {stats.total.total_rps:.1f}")
    
    # Per-endpoint statistics
    print("\n" + "-"*60)
    print("PER-ENDPOINT STATISTICS:")
    print("-"*60)
    
    for name, stat in stats.entries.items():
        if stat.num_requests > 0:
            print(f"\n{name}:")
            print(f"  Requests: {stat.num_requests}")
            print(f"  Failures: {stat.num_failures} ({stat.fail_ratio:.2%})")
            print(f"  Avg: {stat.avg_response_time:.0f}ms")
            print(f"  P95: {stat.get_response_time_percentile(0.95):.0f}ms")
            print(f"  RPS: {stat.total_rps:.1f}")
    
    print("\n" + "="*60 + "\n")


# ============================================================================
# Custom Monitoring
# ============================================================================

class MetricsCollector:
    """Collect custom metrics during load test"""
    
    def __init__(self):
        self.metrics = {
            'searches': 0,
            'autocompletes': 0,
            'clicks': 0,
            'errors': 0,
            'slow_requests': 0  # > 2s
        }
    
    @events.request.add_listener
    def on_request(self, request_type, name, response_time, response_length, exception, **kwargs):
        """Track each request"""
        if 'search' in name:
            self.metrics['searches'] += 1
        elif 'autocomplete' in name:
            self.metrics['autocompletes'] += 1
        elif 'click' in name:
            self.metrics['clicks'] += 1
        
        if exception:
            self.metrics['errors'] += 1
        
        if response_time > 2000:
            self.metrics['slow_requests'] += 1
    
    def get_summary(self):
        """Get metrics summary"""
        return self.metrics


# Initialize collector
metrics_collector = MetricsCollector()
```

### Running Load Tests

```bash
#!/bin/bash
# scripts/run_load_tests.sh

set -e

echo "======================================"
echo "IOS Search - Load Testing Suite"
echo "======================================"

# Configuration
HOST="http://localhost"
RESULTS_DIR="load_test_results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

# ============================================================================
# 1. Baseline Test (Current capacity)
# ============================================================================

echo -e "\n[1/4] Running baseline test..."

locust \
    -f locustfile.py \
    --host="$HOST" \
    --users=100 \
    --spawn-rate=10 \
    --run-time=5m \
    --headless \
    --html="$RESULTS_DIR/baseline.html" \
    --csv="$RESULTS_DIR/baseline"

echo "✓ Baseline test completed"

# ============================================================================
# 2. Normal Load Test (Expected daily traffic)
# ============================================================================

echo -e "\n[2/4] Running normal load test..."

locust \
    -f locustfile.py \
    --host="$HOST" \
    --users=500 \
    --spawn-rate=25 \
    --run-time=10m \
    --headless \
    --html="$RESULTS_DIR/normal_load.html" \
    --csv="$RESULTS_DIR/normal_load"

echo "✓ Normal load test completed"

# ============================================================================
# 3. Peak Load Test (Monday morning rush)
# ============================================================================

echo -e "\n[3/4] Running peak load test..."

locust \
    -f locustfile.py \
    --host="$HOST" \
    --users=1500 \
    --spawn-rate=50 \
    --run-time=10m \
    --headless \
    --html="$RESULTS_DIR/peak_load.html" \
    --csv="$RESULTS_DIR/peak_load"

echo "✓ Peak load test completed"

# ============================================================================
# 4. Stress Test (Find breaking point)
# ============================================================================

echo -e "\n[4/4] Running stress test..."

locust \
    -f locustfile.py \
    --host="$HOST" \
    --users=3000 \
    --spawn-rate=100 \
    --run-time=5m \
    --headless \
    --html="$RESULTS_DIR/stress_test.html" \
    --csv="$RESULTS_DIR/stress_test"

echo "✓ Stress test completed"

# ============================================================================
# Generate Summary Report
# ============================================================================

echo -e "\n======================================"
echo "Generating summary report..."
echo "======================================"

python scripts/analyze_load_tests.py "$RESULTS_DIR"

echo -e "\nResults saved to: $RESULTS_DIR"
echo "Done! 🚀"
```

---

## 📊 Performance Benchmarks

### Component Benchmarks

```python
# scripts/benchmark_components.py

"""
Benchmark individual search components

Tests:
1. Elasticsearch query performance
2. Qdrant vector search performance
3. Redis cache performance
4. Hybrid search fusion
5. End-to-end search latency
"""

import time
import statistics
from typing import List, Dict
from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient
import redis
import numpy as np

class ComponentBenchmark:
    """Benchmark search components"""
    
    def __init__(self):
        self.es_client = Elasticsearch(['http://localhost:9200'])
        self.qdrant_client = QdrantClient(host='localhost', port=6333)
        self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    def benchmark_elasticsearch(self, iterations: int = 100) -> Dict:
        """
        Benchmark Elasticsearch query performance
        
        Measures:
        - Query latency
        - Throughput
        - Cache hit rate
        """
        latencies = []
        
        queries = [
            "persönliches budget",
            "personal assistenz",
            "pflegegeld antrag",
            "schwerbehindertenausweis",
            "eingliederungshilfe"
        ]
        
        print(f"\nBenchmarking Elasticsearch ({iterations} iterations)...")
        
        for i in range(iterations):
            query = queries[i % len(queries)]
            
            start = time.time()
            
            response = self.es_client.search(
                index='ios-documents',
                body={
                    "query": {
                        "multi_match": {
                            "query": query,
                            "fields": ["title^3", "content", "summary^2"],
                            "type": "best_fields"
                        }
                    },
                    "size": 10
                }
            )
            
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
            
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{iterations}")
        
        return {
            'component': 'Elasticsearch',
            'iterations': iterations,
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'mean_ms': statistics.mean(latencies),
            'median_ms': statistics.median(latencies),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'throughput_qps': iterations / (sum(latencies) / 1000)
        }
    
    def benchmark_qdrant(self, iterations: int = 100) -> Dict:
        """
        Benchmark Qdrant vector search
        
        Measures:
        - Vector search latency
        - Throughput
        """
        latencies = []
        
        # Generate random query vectors (384 dimensions for multilingual-e5-small)
        query_vectors = [
            np.random.rand(384).tolist()
            for _ in range(10)
        ]
        
        print(f"\nBenchmarking Qdrant ({iterations} iterations)...")
        
        for i in range(iterations):
            query_vector = query_vectors[i % len(query_vectors)]
            
            start = time.time()
            
            results = self.qdrant_client.search(
                collection_name='ios-embeddings',
                query_vector=query_vector,
                limit=10
            )
            
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
            
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{iterations}")
        
        return {
            'component': 'Qdrant',
            'iterations': iterations,
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'mean_ms': statistics.mean(latencies),
            'median_ms': statistics.median(latencies),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'throughput_qps': iterations / (sum(latencies) / 1000)
        }
    
    def benchmark_redis_cache(self, iterations: int = 1000) -> Dict:
        """
        Benchmark Redis cache performance
        
        Measures:
        - GET latency
        - SET latency
        - Throughput
        """
        get_latencies = []
        set_latencies = []
        
        print(f"\nBenchmarking Redis Cache ({iterations} iterations)...")
        
        for i in range(iterations):
            key = f"benchmark:key:{i % 100}"
            value = f"value_{i}"
            
            # SET
            start = time.time()
            self.redis_client.set(key, value)
            set_latencies.append((time.time() - start) * 1000)
            
            # GET
            start = time.time()
            self.redis_client.get(key)
            get_latencies.append((time.time() - start) * 1000)
            
            if (i + 1) % 200 == 0:
                print(f"  Progress: {i+1}/{iterations}")
        
        return {
            'component': 'Redis Cache',
            'iterations': iterations,
            'get': {
                'min_ms': min(get_latencies),
                'max_ms': max(get_latencies),
                'mean_ms': statistics.mean(get_latencies),
                'p95_ms': np.percentile(get_latencies, 95),
                'p99_ms': np.percentile(get_latencies, 99),
            },
            'set': {
                'min_ms': min(set_latencies),
                'max_ms': max(set_latencies),
                'mean_ms': statistics.mean(set_latencies),
                'p95_ms': np.percentile(set_latencies, 95),
                'p99_ms': np.percentile(set_latencies, 99),
            },
            'throughput_ops': (iterations * 2) / ((sum(get_latencies) + sum(set_latencies)) / 1000)
        }
    
    def benchmark_end_to_end(self, iterations: int = 100) -> Dict:
        """
        Benchmark end-to-end search including:
        - Query processing
        - ES + Qdrant search
        - Result fusion
        - Response formatting
        """
        import requests
        
        latencies = []
        
        queries = [
            "persönliches budget beantragen",
            "hilfe bei behinderung",
            "pflegegeld",
            "eingliederungshilfe",
            "personal assistenz"
        ]
        
        print(f"\nBenchmarking End-to-End Search ({iterations} iterations)...")
        
        for i in range(iterations):
            query = queries[i % len(queries)]
            
            start = time.time()
            
            response = requests.post(
                'http://localhost:8000/api/search/',
                json={'query': query, 'page': 1, 'page_size': 10}
            )
            
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)
            
            if response.status_code != 200:
                print(f"  ERROR: Status {response.status_code}")
            
            if (i + 1) % 20 == 0:
                print(f"  Progress: {i+1}/{iterations}")
        
        return {
            'component': 'End-to-End Search',
            'iterations': iterations,
            'min_ms': min(latencies),
            'max_ms': max(latencies),
            'mean_ms': statistics.mean(latencies),
            'median_ms': statistics.median(latencies),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'throughput_qps': iterations / (sum(latencies) / 1000)
        }
    
    def run_all_benchmarks(self) -> List[Dict]:
        """Run all component benchmarks"""
        results = []
        
        print("="*60)
        print("COMPONENT BENCHMARKS")
        print("="*60)
        
        # Run benchmarks
        results.append(self.benchmark_elasticsearch(iterations=100))
        results.append(self.benchmark_qdrant(iterations=100))
        results.append(self.benchmark_redis_cache(iterations=1000))
        results.append(self.benchmark_end_to_end(iterations=100))
        
        # Print summary
        print("\n" + "="*60)
        print("BENCHMARK RESULTS SUMMARY")
        print("="*60)
        
        for result in results:
            print(f"\n{result['component']}:")
            
            if 'get' in result:
                # Redis has GET/SET
                print(f"  GET:")
                print(f"    Mean: {result['get']['mean_ms']:.2f}ms")
                print(f"    P95: {result['get']['p95_ms']:.2f}ms")
                print(f"    P99: {result['get']['p99_ms']:.2f}ms")
                print(f"  SET:")
                print(f"    Mean: {result['set']['mean_ms']:.2f}ms")
                print(f"    P95: {result['set']['p95_ms']:.2f}ms")
                print(f"    P99: {result['set']['p99_ms']:.2f}ms")
                print(f"  Throughput: {result['throughput_ops']:.0f} ops/sec")
            else:
                print(f"  Mean: {result['mean_ms']:.2f}ms")
                print(f"  Median: {result['median_ms']:.2f}ms")
                print(f"  P95: {result['p95_ms']:.2f}ms")
                print(f"  P99: {result['p99_ms']:.2f}ms")
                print(f"  Throughput: {result['throughput_qps']:.1f} queries/sec")
        
        print("\n" + "="*60)
        
        return results


# Run benchmarks
if __name__ == '__main__':
    benchmark = ComponentBenchmark()
    results = benchmark.run_all_benchmarks()
    
    # Save results to file
    import json
    from datetime import datetime
    
    output_file = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
```

---

## 🎯 Stress Testing

### Finding Breaking Points

```python
# scripts/stress_test.py

"""
Stress Test - Find System Breaking Points

Gradually increases load until system fails
"""

import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class StressTestResult:
    """Results from stress test iteration"""
    concurrent_users: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate: float


class StressTest:
    """
    Progressive stress test
    
    Strategy:
    1. Start with low load
    2. Gradually increase
    3. Measure degradation
    4. Find breaking point
    """
    
    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
        self.test_query = "persönliches budget"
    
    def execute_search(self) -> tuple:
        """Execute single search request"""
        start = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search/",
                json={
                    'query': self.test_query,
                    'page': 1,
                    'page_size': 10
                },
                timeout=30
            )
            
            elapsed_ms = (time.time() - start) * 1000
            
            return (
                response.status_code == 200,
                elapsed_ms
            )
            
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            return (False, elapsed_ms)
    
    def run_iteration(
        self,
        concurrent_users: int,
        duration_seconds: int = 60
    ) -> StressTestResult:
        """
        Run single stress test iteration
        
        Args:
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration
        
        Returns:
            Test results
        """
        print(f"\n  Testing with {concurrent_users} concurrent users...")
        
        start_time = time.time()
        end_time = start_time + duration_seconds
        
        success_count = 0
        failure_count = 0
        response_times = []
        
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            while time.time() < end_time:
                # Submit batch of requests
                futures = [
                    executor.submit(self.execute_search)
                    for _ in range(concurrent_users)
                ]
                
                # Collect results
                for future in as_completed(futures):
                    success, elapsed_ms = future.result()
                    
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                    
                    response_times.append(elapsed_ms)
                
                # Small delay between batches
                time.sleep(0.1)
        
        total_duration = time.time() - start_time
        total_requests = success_count + failure_count
        
        return StressTestResult(
            concurrent_users=concurrent_users,
            total_requests=total_requests,
            successful_requests=success_count,
            failed_requests=failure_count,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p95_response_time_ms=statistics.quantiles(response_times, n=20)[18] if response_times else 0,
            p99_response_time_ms=statistics.quantiles(response_times, n=100)[98] if response_times else 0,
            requests_per_second=total_requests / total_duration,
            error_rate=failure_count / total_requests if total_requests > 0 else 0
        )
    
    def run_progressive_stress_test(self) -> List[StressTestResult]:
        """
        Run progressive stress test
        
        Increases load until:
        - Error rate > 5%
        - P95 latency > 5 seconds
        - System becomes unresponsive
        """
        print("="*60)
        print("PROGRESSIVE STRESS TEST")
        print("="*60)
        print("\nFinding system breaking point...")
        
        results = []
        
        # Test levels
        user_levels = [10, 25, 50, 100, 200, 400, 800, 1600, 3200]
        
        for users in user_levels:
            result = self.run_iteration(
                concurrent_users=users,
                duration_seconds=60
            )
            
            results.append(result)
            
            # Print iteration results
            print(f"    Requests: {result.total_requests}")
            print(f"    Success rate: {(1 - result.error_rate):.1%}")
            print(f"    Avg latency: {result.avg_response_time_ms:.0f}ms")
            print(f"    P95 latency: {result.p95_response_time_ms:.0f}ms")
            print(f"    RPS: {result.requests_per_second:.1f}")
            
            # Check breaking point conditions
            if result.error_rate > 0.05:
                print(f"\n  ⚠️  Breaking point reached: High error rate ({result.error_rate:.1%})")
                break
            
            if result.p95_response_time_ms > 5000:
                print(f"\n  ⚠️  Breaking point reached: High latency ({result.p95_response_time_ms:.0f}ms)")
                break
            
            # Brief pause between iterations
            time.sleep(5)
        
        # Print summary
        self.print_summary(results)
        
        return results
    
    def print_summary(self, results: List[StressTestResult]):
        """Print stress test summary"""
        print("\n" + "="*60)
        print("STRESS TEST SUMMARY")
        print("="*60)
        
        print("\n{:<15} {:<12} {:<15} {:<12} {:<10}".format(
            "Users", "RPS", "Error Rate", "P95 (ms)", "Status"
        ))
        print("-"*60)
        
        for result in results:
            status = "✓ OK"
            if result.error_rate > 0.05:
                status = "✗ HIGH ERROR"
            elif result.p95_response_time_ms > 5000:
                status = "⚠️  SLOW"
            
            print("{:<15} {:<12.1f} {:<15.1%} {:<12.0f} {:<10}".format(
                result.concurrent_users,
                result.requests_per_second,
                result.error_rate,
                result.p95_response_time_ms,
                status
            ))
        
        # Find optimal capacity
        healthy_results = [
            r for r in results
            if r.error_rate < 0.01 and r.p95_response_time_ms < 2000
        ]
        
        if healthy_results:
            best = max(healthy_results, key=lambda x: x.requests_per_second)
            
            print(f"\n✓ Optimal Capacity:")
            print(f"  Concurrent users: {best.concurrent_users}")
            print(f"  Throughput: {best.requests_per_second:.1f} RPS")
            print(f"  P95 latency: {best.p95_response_time_ms:.0f}ms")
        
        print("\n" + "="*60)


# Run stress test
if __name__ == '__main__':
    stress_test = StressTest()
    results = stress_test.run_progressive_stress_test()
    
    # Save results
    import json
    from datetime import datetime
    
    output = {
        'timestamp': datetime.now().isoformat(),
        'results': [
            {
                'concurrent_users': r.concurrent_users,
                'total_requests': r.total_requests,
                'error_rate': r.error_rate,
                'avg_response_time_ms': r.avg_response_time_ms,
                'p95_response_time_ms': r.p95_response_time_ms,
                'requests_per_second': r.requests_per_second
            }
            for r in results
        ]
    }
    
    with open('stress_test_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nResults saved to: stress_test_results.json")
```

---

## 🌪️ Chaos Engineering

### Fault Injection Tests

```python
# scripts/chaos_tests.py

"""
Chaos Engineering for Search System

Test system resilience by injecting failures:
1. Elasticsearch node failure
2. Qdrant unavailability
3. Redis cache failure
4. Network latency
5. Partial data loss
"""

import docker
import time
import requests
from typing import Dict, List

class ChaosTest:
    """
    Chaos engineering tests
    
    Simulates real-world failures to test resilience
    """
    
    def __init__(self):
        self.docker_client = docker.from_env()
        self.base_url = 'http://localhost:8000'
    
    def test_elasticsearch_failure(self):
        """
        Test: Elasticsearch node failure
        
        Expected behavior:
        - Search continues with degraded performance
        - Fallback to cache
        - Graceful error handling
        """
        print("\n" + "="*60)
        print("CHAOS TEST: Elasticsearch Node Failure")
        print("="*60)
        
        # Get Elasticsearch containers
        es_containers = [
            c for c in self.docker_client.containers.list()
            if 'elasticsearch' in c.name
        ]
        
        if not es_containers:
            print("  ⚠️  No Elasticsearch containers found")
            return
        
        # Stop one data node
        es_node = es_containers[0]
        print(f"\n  1. Stopping Elasticsearch node: {es_node.name}")
        es_node.stop()
        
        time.sleep(5)
        
        # Test search during failure
        print("  2. Testing search during node failure...")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search/",
                json={'query': 'test', 'page': 1, 'page_size': 10},
                timeout=10
            )
            
            if response.status_code == 200:
                print("     ✓ Search still functional (degraded)")
                data = response.json()
                print(f"     Results: {len(data.get('results', []))}")
            else:
                print(f"     ✗ Search failed: {response.status_code}")
        
        except Exception as e:
            print(f"     ✗ Error: {e}")
        
        # Restart node
        print(f"  3. Restarting Elasticsearch node...")
        es_node.start()
        
        time.sleep(10)
        
        # Test recovery
        print("  4. Testing recovery...")
        
        response = requests.post(
            f"{self.base_url}/api/search/",
            json={'query': 'test', 'page': 1, 'page_size': 10}
        )
        
        if response.status_code == 200:
            print("     ✓ System recovered")
        else:
            print("     ✗ Recovery failed")
        
        print("\n  Test completed!")
    
    def test_cache_failure(self):
        """
        Test: Redis cache failure
        
        Expected behavior:
        - Searches continue (slower)
        - Direct backend queries
        - No data loss
        """
        print("\n" + "="*60)
        print("CHAOS TEST: Redis Cache Failure")
        print("="*60)
        
        # Get Redis container
        redis_containers = [
            c for c in self.docker_client.containers.list()
            if 'redis' in c.name
        ]
        
        if not redis_containers:
            print("  ⚠️  No Redis containers found")
            return
        
        redis_container = redis_containers[0]
        
        # Measure baseline performance
        print("\n  1. Measuring baseline (with cache)...")
        baseline = self._measure_search_performance(iterations=10)
        print(f"     Avg latency: {baseline['avg_ms']:.0f}ms")
        
        # Stop Redis
        print(f"  2. Stopping Redis: {redis_container.name}")
        redis_container.stop()
        
        time.sleep(2)
        
        # Measure degraded performance
        print("  3. Measuring degraded performance (no cache)...")
        degraded = self._measure_search_performance(iterations=10)
        print(f"     Avg latency: {degraded['avg_ms']:.0f}ms")
        print(f"     Degradation: {(degraded['avg_ms'] / baseline['avg_ms'] - 1) * 100:.1f}%")
        
        # Restart Redis
        print("  4. Restarting Redis...")
        redis_container.start()
        
        time.sleep(5)
        
        # Measure recovery
        print("  5. Measuring recovery...")
        recovery = self._measure_search_performance(iterations=10)
        print(f"     Avg latency: {recovery['avg_ms']:.0f}ms")
        
        if abs(recovery['avg_ms'] - baseline['avg_ms']) < 50:
            print("     ✓ Performance recovered")
        else:
            print("     ⚠️  Performance not fully recovered")
        
        print("\n  Test completed!")
    
    def test_network_latency(self):
        """
        Test: Simulate network latency
        
        Uses tc (traffic control) to add latency
        """
        print("\n" + "="*60)
        print("CHAOS TEST: Network Latency")
        print("="*60)
        
        print("\n  Note: Requires 'tc' (traffic control) command")
        print("  This test adds 200ms latency to all network traffic")
        print("  Run manually with:")
        print("    sudo tc qdisc add dev eth0 root netem delay 200ms")
        print("    # Run tests")
        print("    sudo tc qdisc del dev eth0 root")
    
    def _measure_search_performance(self, iterations: int = 10) -> Dict:
        """Helper: Measure search performance"""
        latencies = []
        
        for _ in range(iterations):
            start = time.time()
            
            try:
                response = requests.post(
                    f"{self.base_url}/api/search/",
                    json={'query': 'test', 'page': 1, 'page_size': 10},
                    timeout=30
                )
                
                if response.status_code == 200:
                    elapsed_ms = (time.time() - start) * 1000
                    latencies.append(elapsed_ms)
            
            except Exception:
                pass
        
        if latencies:
            import statistics
            return {
                'avg_ms': statistics.mean(latencies),
                'min_ms': min(latencies),
                'max_ms': max(latencies)
            }
        
        return {'avg_ms': 0, 'min_ms': 0, 'max_ms': 0}
    
    def run_all_chaos_tests(self):
        """Run all chaos tests"""
        print("\n" + "="*60)
        print("CHAOS ENGINEERING TEST SUITE")
        print("="*60)
        
        self.test_elasticsearch_failure()
        self.test_cache_failure()
        self.test_network_latency()
        
        print("\n" + "="*60)
        print("All chaos tests completed!")
        print("="*60)


# Run chaos tests
if __name__ == '__main__':
    chaos = ChaosTest()
    chaos.run_all_chaos_tests()
```

---

**Продолжение следует...**

Создано:
- ✅ Locust load testing configuration
- ✅ Component benchmarking suite
- ✅ Progressive stress testing
- ✅ Chaos engineering tests
- ✅ Performance measurement tools
- ✅ Automated test scripts

**Следующие разделы:**
1. Performance Tuning Guide
2. Cost Optimization
3. Disaster Recovery
4. Production Readiness Checklist

**Готовы продолжить с Performance Tuning?**