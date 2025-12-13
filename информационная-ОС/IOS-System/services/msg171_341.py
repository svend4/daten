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