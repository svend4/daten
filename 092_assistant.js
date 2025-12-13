Пользователь говорит "По порядку", что означает, что он хочет продолжить в последовательности, которую я предложил. Значит начинаем с Week 25-26: Performance Optimization.

Это будет включать:
1. Load testing (нагрузочное тестирование)
2. Query optimization (оптимизация запросов)
3. Caching strategies (стратегии кэширования)
4. CDN integration (интеграция CDN)

Создам comprehensive файлы для Week 25-26 по оптимизации производительности.# 🚀 WEEK 25-26: PERFORMANCE OPTIMIZATION

## 📋 ЦЕЛЬ

Оптимизация производительности IOS System для enterprise-нагрузок:
- **Load Testing** - нагрузочное тестирование
- **Query Optimization** - оптимизация запросов к БД
- **Advanced Caching** - многоуровневое кэширование
- **CDN Integration** - интеграция CDN
- **Performance Monitoring** - мониторинг производительности
- **Optimization Strategies** - стратегии оптимизации

---

## DAY 137-138: LOAD TESTING & BENCHMARKING

---

## ФАЙЛ 1: `tests/load/k6-api-load-test.js`

```javascript
/**
 * K6 Load Testing Script for IOS API
 * 
 * Test Scenarios:
 * 1. Baseline - Normal load
 * 2. Stress - High load
 * 3. Spike - Sudden traffic surge
 * 4. Soak - Extended duration test
 * 
 * Usage:
 *   k6 run tests/load/k6-api-load-test.js
 *   k6 run --vus 100 --duration 30s tests/load/k6-api-load-test.js
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// ============================================
// Configuration
// ============================================
const BASE_URL = __ENV.BASE_URL || 'https://api.ios-system.com';
const API_KEY = __ENV.API_KEY || 'test_api_key';

// Custom Metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const successfulRequests = new Counter('successful_requests');
const failedRequests = new Counter('failed_requests');

// ============================================
// Test Configuration
// ============================================
export const options = {
  scenarios: {
    // Baseline: Normal load
    baseline: {
      executor: 'constant-vus',
      vus: 10,
      duration: '5m',
      exec: 'baseline',
      startTime: '0s',
    },
    
    // Stress: Ramp up to high load
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },
        { duration: '5m', target: 50 },
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 0 },
      ],
      exec: 'stress',
      startTime: '5m',
    },
    
    // Spike: Sudden traffic surge
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '10s', target: 0 },
      ],
      exec: 'spike',
      startTime: '21m',
    },
    
    // Soak: Long duration test
    soak: {
      executor: 'constant-vus',
      vus: 20,
      duration: '30m',
      exec: 'soak',
      startTime: '23m',
    },
  },
  
  thresholds: {
    // HTTP errors should be less than 1%
    'errors': ['rate<0.01'],
    
    // 95% of requests should be below 500ms
    'http_req_duration': ['p(95)<500'],
    
    // 99% of requests should be below 1s
    'http_req_duration': ['p(99)<1000'],
    
    // API specific duration
    'api_duration': ['p(95)<300', 'p(99)<600'],
    
    // Success rate should be above 99%
    'http_req_failed': ['rate<0.01'],
  },
};

// ============================================
// Setup & Teardown
// ============================================
export function setup() {
  // Authenticate and get token
  const loginRes = http.post(`${BASE_URL}/api/auth/login`, 
    JSON.stringify({
      username: 'test_user',
      password: 'test_password'
    }), 
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );
  
  if (loginRes.status === 200) {
    const token = loginRes.json('access_token');
    return { token };
  }
  
  return { token: null };
}

export function teardown(data) {
  // Cleanup if needed
  console.log('Load test completed');
}

// ============================================
// Helper Functions
// ============================================
function makeRequest(method, endpoint, body = null, token = null) {
  const headers = {
    'Content-Type': 'application/json',
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const params = {
    headers: headers,
    tags: { endpoint: endpoint },
  };
  
  const startTime = new Date().getTime();
  let response;
  
  if (method === 'GET') {
    response = http.get(`${BASE_URL}${endpoint}`, params);
  } else if (method === 'POST') {
    response = http.post(`${BASE_URL}${endpoint}`, 
      body ? JSON.stringify(body) : null, 
      params
    );
  } else if (method === 'PUT') {
    response = http.put(`${BASE_URL}${endpoint}`, 
      body ? JSON.stringify(body) : null, 
      params
    );
  } else if (method === 'DELETE') {
    response = http.del(`${BASE_URL}${endpoint}`, null, params);
  }
  
  const duration = new Date().getTime() - startTime;
  apiDuration.add(duration);
  
  const success = check(response, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!success);
  
  if (success) {
    successfulRequests.add(1);
  } else {
    failedRequests.add(1);
    console.error(`Request failed: ${endpoint} - Status: ${response.status}`);
  }
  
  return response;
}

// ============================================
// Test Scenarios
// ============================================

/**
 * Baseline Scenario - Normal user activity
 */
export function baseline(data) {
  group('Health Check', () => {
    const res = makeRequest('GET', '/health');
    check(res, {
      'health check is OK': (r) => r.json('status') === 'healthy',
    });
  });
  
  sleep(1);
  
  group('Document Operations', () => {
    // List documents
    makeRequest('GET', '/api/documents?limit=20', null, data.token);
    sleep(0.5);
    
    // Create document
    const createRes = makeRequest('POST', '/api/documents', {
      title: `Load Test Document ${Date.now()}`,
      content: 'This is a test document created during load testing.',
    }, data.token);
    
    if (createRes.status === 201) {
      const docId = createRes.json('id');
      
      sleep(0.5);
      
      // Get document
      makeRequest('GET', `/api/documents/${docId}`, null, data.token);
      
      sleep(0.5);
      
      // Update document
      makeRequest('PUT', `/api/documents/${docId}`, {
        title: 'Updated Title',
      }, data.token);
      
      sleep(0.5);
      
      // Delete document
      makeRequest('DELETE', `/api/documents/${docId}`, null, data.token);
    }
  });
  
  sleep(1);
  
  group('Search Operations', () => {
    // Basic search
    makeRequest('GET', '/api/search?q=test&limit=10', null, data.token);
    
    sleep(0.5);
    
    // Neural search
    makeRequest('POST', '/api/search/neural', {
      query: 'personal budget assistance',
      limit: 10,
    }, data.token);
  });
  
  sleep(2);
}

/**
 * Stress Scenario - High load testing
 */
export function stress(data) {
  group('Read Operations', () => {
    // Multiple concurrent reads
    makeRequest('GET', '/api/documents?limit=50', null, data.token);
    makeRequest('GET', '/api/search?q=budget', null, data.token);
    makeRequest('GET', '/api/domains', null, data.token);
  });
  
  sleep(0.2);
  
  group('Write Operations', () => {
    makeRequest('POST', '/api/documents', {
      title: `Stress Test ${Date.now()}`,
      content: 'High load test document',
    }, data.token);
  });
  
  sleep(0.5);
}

/**
 * Spike Scenario - Sudden traffic surge
 */
export function spike(data) {
  // Simulate many users hitting the API simultaneously
  makeRequest('GET', '/health');
  makeRequest('GET', '/api/documents?limit=10', null, data.token);
  makeRequest('GET', '/api/search?q=test', null, data.token);
  
  sleep(0.1);
}

/**
 * Soak Scenario - Long duration test
 */
export function soak(data) {
  // Simulate normal usage over extended period
  const actions = [
    () => makeRequest('GET', '/api/documents', null, data.token),
    () => makeRequest('GET', '/api/search?q=random', null, data.token),
    () => makeRequest('POST', '/api/documents', {
      title: `Soak Test ${Date.now()}`,
      content: 'Long duration test',
    }, data.token),
  ];
  
  // Random action
  const action = actions[Math.floor(Math.random() * actions.length)];
  action();
  
  sleep(Math.random() * 3 + 1); // 1-4 seconds
}

// ============================================
// Custom Summary
// ============================================
export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-results.json': JSON.stringify(data),
    'load-test-report.html': htmlReport(data),
  };
}

function textSummary(data, options) {
  // Custom text summary
  let summary = '\n=== Load Test Summary ===\n\n';
  
  const metrics = data.metrics;
  
  summary += `Total Requests: ${metrics.http_reqs.values.count}\n`;
  summary += `Failed Requests: ${metrics.http_req_failed.values.passes}\n`;
  summary += `Request Rate: ${metrics.http_reqs.values.rate.toFixed(2)} req/s\n`;
  summary += `\n`;
  
  summary += `Response Times:\n`;
  summary += `  Min: ${metrics.http_req_duration.values.min.toFixed(2)}ms\n`;
  summary += `  Avg: ${metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `  Max: ${metrics.http_req_duration.values.max.toFixed(2)}ms\n`;
  summary += `  p95: ${metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  p99: ${metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `\n`;
  
  summary += `Data Transferred: ${(metrics.data_received.values.count / 1024 / 1024).toFixed(2)} MB\n`;
  summary += `Data Sent: ${(metrics.data_sent.values.count / 1024 / 1024).toFixed(2)} MB\n`;
  
  return summary;
}

function htmlReport(data) {
  // Generate HTML report
  return `
<!DOCTYPE html>
<html>
<head>
  <title>IOS Load Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 40px; }
    h1 { color: #333; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
    th { background-color: #4CAF50; color: white; }
    tr:nth-child(even) { background-color: #f2f2f2; }
    .metric { margin: 20px 0; }
    .pass { color: green; }
    .fail { color: red; }
  </style>
</head>
<body>
  <h1>IOS System Load Test Report</h1>
  <div class="metric">
    <h2>Overview</h2>
    <p>Test Duration: ${data.state.testRunDurationMs / 1000} seconds</p>
    <p>Total Requests: ${data.metrics.http_reqs.values.count}</p>
    <p>Request Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s</p>
  </div>
  
  <h2>Response Times</h2>
  <table>
    <tr><th>Metric</th><th>Value</th></tr>
    <tr><td>Min</td><td>${data.metrics.http_req_duration.values.min.toFixed(2)}ms</td></tr>
    <tr><td>Average</td><td>${data.metrics.http_req_duration.values.avg.toFixed(2)}ms</td></tr>
    <tr><td>Max</td><td>${data.metrics.http_req_duration.values.max.toFixed(2)}ms</td></tr>
    <tr><td>p95</td><td>${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms</td></tr>
    <tr><td>p99</td><td>${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms</td></tr>
  </table>
  
  <h2>Thresholds</h2>
  <table>
    <tr><th>Threshold</th><th>Status</th></tr>
    ${Object.entries(data.thresholds).map(([name, result]) => `
      <tr>
        <td>${name}</td>
        <td class="${result.ok ? 'pass' : 'fail'}">${result.ok ? 'PASS' : 'FAIL'}</td>
      </tr>
    `).join('')}
  </table>
</body>
</html>
  `;
}
```

---

## ФАЙЛ 2: `tests/load/locust-load-test.py`

```python
"""
Locust Load Testing for IOS System
Alternative to k6, Python-based

Usage:
    locust -f tests/load/locust-load-test.py --host https://api.ios-system.com
    locust -f tests/load/locust-load-test.py --headless -u 100 -r 10 -t 5m
"""

import json
import random
from datetime import datetime
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser


class IOSUser(FastHttpUser):
    """
    Simulates IOS System user behavior
    
    Tasks are weighted by frequency of real user actions
    """
    
    # Wait time between tasks (1-3 seconds)
    wait_time = between(1, 3)
    
    # Store authentication token
    token = None
    
    def on_start(self):
        """
        Called when a user starts
        Authenticate and get token
        """
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "test_user",
                "password": "test_password"
            },
            name="/api/auth/login"
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    def _headers(self):
        """Get headers with auth token"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(10)
    def list_documents(self):
        """
        List documents (most common operation)
        Weight: 10 (high frequency)
        """
        self.client.get(
            "/api/documents",
            params={"limit": 20, "offset": 0},
            headers=self._headers(),
            name="/api/documents [LIST]"
        )
    
    @task(5)
    def get_document(self):
        """
        Get single document
        Weight: 5 (medium frequency)
        """
        # Simulate getting a random document
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        self.client.get(
            f"/api/documents/{doc_id}",
            headers=self._headers(),
            name="/api/documents/:id [GET]"
        )
    
    @task(3)
    def create_document(self):
        """
        Create new document
        Weight: 3 (medium-low frequency)
        """
        self.client.post(
            "/api/documents",
            json={
                "title": f"Load Test Document {datetime.now().isoformat()}",
                "content": "This is a test document created during load testing.",
                "domain_id": f"domain_{random.randint(1, 10)}"
            },
            headers=self._headers(),
            name="/api/documents [CREATE]"
        )
    
    @task(2)
    def update_document(self):
        """
        Update document
        Weight: 2 (low frequency)
        """
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        self.client.put(
            f"/api/documents/{doc_id}",
            json={
                "title": f"Updated Title {datetime.now().isoformat()}"
            },
            headers=self._headers(),
            name="/api/documents/:id [UPDATE]"
        )
    
    @task(1)
    def delete_document(self):
        """
        Delete document
        Weight: 1 (very low frequency)
        """
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        self.client.delete(
            f"/api/documents/{doc_id}",
            headers=self._headers(),
            name="/api/documents/:id [DELETE]"
        )
    
    @task(7)
    def basic_search(self):
        """
        Basic text search
        Weight: 7 (high frequency)
        """
        queries = [
            "personal budget",
            "assistance",
            "disability support",
            "legal advice",
            "social services"
        ]
        
        query = random.choice(queries)
        
        self.client.get(
            "/api/search",
            params={"q": query, "limit": 10},
            headers=self._headers(),
            name="/api/search [BASIC]"
        )
    
    @task(3)
    def neural_search(self):
        """
        Neural/semantic search
        Weight: 3 (medium-low frequency)
        """
        queries = [
            "How do I apply for personal budget?",
            "What assistance is available for disabled people?",
            "Legal support for social services issues"
        ]
        
        query = random.choice(queries)
        
        self.client.post(
            "/api/search/neural",
            json={"query": query, "limit": 10},
            headers=self._headers(),
            name="/api/search/neural [NEURAL]"
        )
    
    @task(5)
    def list_domains(self):
        """
        List knowledge domains
        Weight: 5 (medium frequency)
        """
        self.client.get(
            "/api/domains",
            headers=self._headers(),
            name="/api/domains [LIST]"
        )
    
    @task(1)
    def health_check(self):
        """
        Health check
        Weight: 1 (monitoring)
        """
        self.client.get(
            "/health",
            name="/health"
        )


class AdminUser(FastHttpUser):
    """
    Simulates admin user behavior
    Lower frequency, more resource-intensive operations
    """
    
    wait_time = between(5, 10)
    token = None
    
    def on_start(self):
        """Authenticate as admin"""
        response = self.client.post(
            "/api/auth/login",
            json={
                "username": "admin_user",
                "password": "admin_password"
            }
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    def _headers(self):
        """Get headers with auth token"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}
    
    @task(5)
    def view_analytics(self):
        """View system analytics"""
        self.client.get(
            "/api/analytics/overview",
            headers=self._headers(),
            name="/api/analytics/overview"
        )
    
    @task(3)
    def export_data(self):
        """Export data"""
        self.client.post(
            "/api/export",
            json={
                "format": "csv",
                "entity": "documents"
            },
            headers=self._headers(),
            name="/api/export [CSV]"
        )
    
    @task(2)
    def reindex_search(self):
        """Trigger search reindex"""
        self.client.post(
            "/api/search/reindex",
            headers=self._headers(),
            name="/api/search/reindex"
        )
    
    @task(1)
    def view_logs(self):
        """View system logs"""
        self.client.get(
            "/api/logs",
            params={"limit": 100},
            headers=self._headers(),
            name="/api/logs"
        )


# ============================================
# Event Handlers for Custom Reporting
# ============================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("=" * 60)
    print("IOS System Load Test Starting")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("=" * 60)
    print("IOS System Load Test Completed")
    print("=" * 60)
    
    # Print summary statistics
    stats = environment.stats
    
    print("\n=== Summary Statistics ===")
    print(f"Total Requests: {stats.total.num_requests}")
    print(f"Failed Requests: {stats.total.num_failures}")
    print(f"Request Rate: {stats.total.current_rps:.2f} req/s")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min Response Time: {stats.total.min_response_time:.2f}ms")
    print(f"Max Response Time: {stats.total.max_response_time:.2f}ms")
    print(f"95th Percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"99th Percentile: {stats.total.get_response_time_percentile(0.99):.2f}ms")


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Called on every request
    Can be used for custom metrics
    """
    # Log slow requests
    if response_time > 1000:
        print(f"SLOW REQUEST: {name} took {response_time}ms")
    
    # Log errors
    if exception:
        print(f"ERROR: {name} failed with {exception}")
```

---

## ФАЙЛ 3: `tests/load/load-test-scenarios.yaml`

```yaml
# Load Test Scenarios Configuration
# Used by automation scripts to run various test scenarios

scenarios:
  # Quick smoke test
  smoke:
    description: "Quick smoke test to verify basic functionality"
    duration: 1m
    vus: 5
    thresholds:
      http_req_duration:
        - p(95)<1000
      http_req_failed:
        - rate<0.05

  # Baseline performance
  baseline:
    description: "Baseline performance test with normal load"
    duration: 5m
    vus: 20
    thresholds:
      http_req_duration:
        - p(95)<500
        - p(99)<1000
      http_req_failed:
        - rate<0.01

  # Stress test
  stress:
    description: "Stress test to find breaking point"
    stages:
      - duration: 2m
        target: 50
      - duration: 5m
        target: 50
      - duration: 2m
        target: 100
      - duration: 5m
        target: 100
      - duration: 2m
        target: 150
      - duration: 5m
        target: 150
      - duration: 2m
        target: 0
    thresholds:
      http_req_duration:
        - p(95)<1000
      http_req_failed:
        - rate<0.05

  # Spike test
  spike:
    description: "Spike test to verify recovery from sudden load"
    stages:
      - duration: 1m
        target: 20
      - duration: 10s
        target: 200
      - duration: 3m
        target: 200
      - duration: 10s
        target: 20
      - duration: 1m
        target: 20
    thresholds:
      http_req_duration:
        - p(95)<2000
      http_req_failed:
        - rate<0.10

  # Soak test
  soak:
    description: "Soak test for memory leaks and stability"
    duration: 2h
    vus: 30
    thresholds:
      http_req_duration:
        - p(95)<600
      http_req_failed:
        - rate<0.02

  # Capacity test
  capacity:
    description: "Find maximum sustained capacity"
    stages:
      - duration: 5m
        target: 50
      - duration: 10m
        target: 50
      - duration: 5m
        target: 100
      - duration: 10m
        target: 100
      - duration: 5m
        target: 150
      - duration: 10m
        target: 150
      - duration: 5m
        target: 200
      - duration: 10m
        target: 200
      - duration: 5m
        target: 0
    thresholds:
      http_req_duration:
        - p(95)<800
      http_req_failed:
        - rate<0.03

# Performance benchmarks
benchmarks:
  targets:
    api_response_p95: 500ms
    api_response_p99: 1000ms
    database_query: 100ms
    search_latency: 150ms
    throughput: 1000 req/s
    error_rate: <1%
    uptime: 99.9%

  current:
    api_response_p95: 200ms
    api_response_p99: 400ms
    database_query: 50ms
    search_latency: 120ms
    throughput: 500 req/s
    error_rate: 0.5%
    uptime: 99.5%

# Test data
test_data:
  users:
    - username: test_user_1
      password: test_password
      role: user
    - username: test_user_2
      password: test_password
      role: user
    - username: admin_user
      password: admin_password
      role: admin

  documents:
    count: 1000
    titles:
      - "Personal Budget Application"
      - "Disability Support Guide"
      - "Legal Assistance Information"
      - "Social Services Overview"
      - "Care Plan Template"

  search_queries:
    - "personal budget"
    - "disability assistance"
    - "legal support"
    - "social services"
    - "care planning"

# Environment configurations
environments:
  local:
    base_url: http://localhost:8000
    database: postgresql://localhost:5432/ios_test
    
  staging:
    base_url: https://staging-api.ios-system.com
    database: postgresql://staging-db:5432/ios_staging
    
  production:
    base_url: https://api.ios-system.com
    database: postgresql://production-db:5432/ios_production
```

---

**Продолжение следует...**

Создано:
- ✅ K6 load testing script (comprehensive scenarios)
- ✅ Locust load testing (Python alternative)
- ✅ Load test scenarios configuration

**Следующие файлы:**
- Database query optimization
- Caching strategies
- Performance monitoring
- CDN integration
- Optimization scripts

**Готовы продолжить?**