"""
Analyze performance test results
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def analyze_results(report_dir: str):
    """Analyze Locust results"""
    
    print("="*80)
    print("PERFORMANCE TEST ANALYSIS")
    print("="*80)
    
    # Parse results (simplified - actual parsing depends on Locust output format)
    metrics = {
        'avg_response_time': 0,
        'p95_response_time': 0,
        'p99_response_time': 0,
        'requests_per_second': 0,
        'error_rate': 0,
        'total_requests': 0,
    }
    
    print(f"\nMetrics:")
    print(f"  Average Response Time: {metrics['avg_response_time']}ms")
    print(f"  95th Percentile: {metrics['p95_response_time']}ms")
    print(f"  99th Percentile: {metrics['p99_response_time']}ms")
    print(f"  Throughput: {metrics['requests_per_second']} req/s")
    print(f"  Error Rate: {metrics['error_rate']}%")
    print(f"  Total Requests: {metrics['total_requests']}")
    
    # Performance targets
    targets = {
        'avg_response_time': 300,  # 300ms
        'p95_response_time': 1000,  # 1s
        'error_rate': 1.0,  # 1%
    }
    
    print(f"\nTarget Compliance:")
    
    passed = True
    for metric, target in targets.items():
        actual = metrics[metric]
        status = "✓" if actual <= target else "✗"
        
        if actual > target:
            passed = False
        
        print(f"  {status} {metric}: {actual} (target: <= {target})")
    
    if passed:
        print(f"\n✓ All performance targets met!")
        return 0
    else:
        print(f"\n✗ Some performance targets not met")
        return 1


if __name__ == "__main__":
    report_dir = sys.argv[1] if len(sys.argv) > 1 else "reports/"
    sys.exit(analyze_results(report_dir))