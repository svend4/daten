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