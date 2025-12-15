"""
Benchmark search performance: Whoosh vs Elasticsearch
"""

import asyncio
import time
import statistics
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ios_core.search.elasticsearch_service import ElasticsearchService
from ios_core.services.search import SearchService  # Old Whoosh service


async def benchmark_search_engine(
    service,
    queries: List[str],
    iterations: int = 10
) -> dict:
    """Benchmark search service"""
    
    results = {
        "queries": len(queries),
        "iterations": iterations,
        "times": [],
        "avg_time": 0,
        "median_time": 0,
        "min_time": 0,
        "max_time": 0,
        "p95_time": 0
    }
    
    # Warm up
    for query in queries[:5]:
        await service.search(query, limit=10)
    
    # Benchmark
    for _ in range(iterations):
        for query in queries:
            start = time.time()
            await service.search(query, limit=10)
            duration = (time.time() - start) * 1000  # ms
            results["times"].append(duration)
    
    # Calculate statistics
    times = results["times"]
    results["avg_time"] = statistics.mean(times)
    results["median_time"] = statistics.median(times)
    results["min_time"] = min(times)
    results["max_time"] = max(times)
    results["p95_time"] = statistics.quantiles(times, n=20)[18]  # 95th percentile
    
    return results


async def main():
    """Run benchmark"""
    
    print("="*80)
    print("SEARCH PERFORMANCE BENCHMARK")
    print("="*80)
    print()
    
    # Test queries
    queries = [
        "Persönliches Budget",
        "Widerspruch Bescheid",
        "§29 SGB IX",
        "Eingliederungshilfe",
        "Bezirk Oberbayern",
        "Schwerbehinderung",
        "Teilhabe Leistung",
        "Antrag Sozialamt",
        "Urteil Sozialgericht",
        "Beratung Hilfe"
    ]
    
    print(f"Test queries: {len(queries)}")
    print(f"Iterations: 10")
    print()
    
    # Benchmark Whoosh
    print("Benchmarking Whoosh...")
    whoosh_service = SearchService()
    whoosh_results = await benchmark_search_engine(whoosh_service, queries)
    
    print(f"  Avg: {whoosh_results['avg_time']:.2f}ms")
    print(f"  Median: {whoosh_results['median_time']:.2f}ms")
    print(f"  P95: {whoosh_results['p95_time']:.2f}ms")
    print()
    
    # Benchmark Elasticsearch
    print("Benchmarking Elasticsearch...")
    es_service = ElasticsearchService()
    await es_service.initialize()
    
    es_results = await benchmark_search_engine(es_service, queries)
    
    print(f"  Avg: {es_results['avg_time']:.2f}ms")
    print(f"  Median: {es_results['median_time']:.2f}ms")
    print(f"  P95: {es_results['p95_time']:.2f}ms")
    print()
    
    # Comparison
    print("="*80)
    print("COMPARISON")
    print("="*80)
    print()
    
    speedup_avg = whoosh_results['avg_time'] / es_results['avg_time']
    speedup_p95 = whoosh_results['p95_time'] / es_results['p95_time']
    
    print(f"Average time:")
    print(f"  Whoosh: {whoosh_results['avg_time']:.2f}ms")
    print(f"  Elasticsearch: {es_results['avg_time']:.2f}ms")
    print(f"  Speedup: {speedup_avg:.2f}x")
    print()
    
    print(f"P95 latency:")
    print(f"  Whoosh: {whoosh_results['p95_time']:.2f}ms")
    print(f"  Elasticsearch: {es_results['p95_time']:.2f}ms")
    print(f"  Speedup: {speedup_p95:.2f}x")
    print()
    
    # Winner
    if es_results['avg_time'] < whoosh_results['avg_time']:
        print("✓ Elasticsearch is faster!")
    else:
        print("✓ Whoosh is faster!")
    
    await es_service.close()


if __name__ == "__main__":
    asyncio.run(main())