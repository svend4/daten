"""
Load testing with Locust
"""

from locust import HttpUser, task, between
import random


class IOSUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token"""
        response = self.client.post("/api/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}
    
    @task(3)
    def search_documents(self):
        """Search for documents"""
        queries = [
            "Persönliches Budget",
            "§29 SGB IX",
            "Widerspruch",
            "Eingliederungshilfe",
            "Teilhabe"
        ]
        
        self.client.post("/api/search/", headers=self.headers, json={
            "query": random.choice(queries),
            "search_type": "hybrid",
            "limit": 10
        })
    
    @task(1)
    def get_document(self):
        """Get random document"""
        # In real test, use actual document IDs from database
        doc_id = f"test_doc_{random.randint(1, 100)}"
        self.client.get(f"/api/documents/{doc_id}", headers=self.headers)
    
    @task(1)
    def autocomplete(self):
        """Test autocomplete"""
        prefixes = ["Per", "Wid", "§2", "SGB", "Ein"]
        
        self.client.get(
            f"/api/search/suggest?prefix={random.choice(prefixes)}",
            headers=self.headers
        )