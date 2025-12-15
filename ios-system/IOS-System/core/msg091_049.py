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