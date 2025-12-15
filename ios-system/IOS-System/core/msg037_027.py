"""
Comprehensive load testing suite
"""

from locust import HttpUser, task, between, TaskSet
import random
import json


class DocumentManagementTasks(TaskSet):
    """Document management operations"""
    
    @task(3)
    def search_documents(self):
        """Search operations - most common"""
        queries = [
            "Persönliches Budget",
            "§29 SGB IX",
            "Widerspruch Bescheid",
            "Eingliederungshilfe",
            "Bezirk Oberbayern"
        ]
        
        self.client.post("/api/search/", json={
            "query": random.choice(queries),
            "search_type": random.choice(["full_text", "semantic", "hybrid"]),
            "limit": 10
        }, headers=self.headers)
    
    @task(2)
    def list_documents(self):
        """List documents with pagination"""
        self.client.get(
            f"/api/documents/?limit=20&offset={random.randint(0, 100)}",
            headers=self.headers
        )
    
    @task(1)
    def get_document(self):
        """Get specific document"""
        # In real test, use actual document IDs
        doc_id = f"doc_{random.randint(1, 1000)}"
        self.client.get(f"/api/documents/{doc_id}", headers=self.headers)
    
    @task(1)
    def autocomplete(self):
        """Autocomplete search"""
        prefixes = ["Per", "Wid", "§2", "SGB", "Ein"]
        self.client.get(
            f"/api/search/suggest?prefix={random.choice(prefixes)}",
            headers=self.headers
        )


class AdminTasks(TaskSet):
    """Admin operations"""
    
    @task(2)
    def view_dashboard(self):
        """View dashboard statistics"""
        self.client.get("/api/analytics/dashboard", headers=self.headers)
    
    @task(1)
    def graph_statistics(self):
        """View knowledge graph stats"""
        self.client.get("/api/graph/SGB-IX/statistics", headers=self.headers)


class IOSUser(HttpUser):
    """Simulated IOS user"""
    
    wait_time = between(1, 3)
    tasks = [DocumentManagementTasks, AdminTasks]
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            self.headers = {}


class HeavyLoadUser(HttpUser):
    """Simulated heavy user (document uploads)"""
    
    wait_time = between(5, 15)
    
    def on_start(self):
        """Login"""
        response = self.client.post("/api/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
    
    @task
    def upload_document(self):
        """Upload document (heavy operation)"""
        # Create dummy file
        files = {
            'file': ('test.txt', b'Test document content ' * 100, 'text/plain')
        }
        
        self.client.post(
            "/api/documents/upload?domain_name=Test",
            files=files,
            headers=self.headers
        )