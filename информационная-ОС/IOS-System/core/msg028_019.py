# Performance testing
# tests/performance/test_load.py

from locust import HttpUser, task, between

class IOSUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def search_documents(self):
        self.client.post("/api/search", json={
            "query": "Persönliches Budget",
            "limit": 10
        })
    
    @task(3)
    def upload_document(self):
        with open("test_data/sample.pdf", "rb") as f:
            self.client.post("/api/documents/upload", 
                files={"file": f},
                data={"domain_name": "SGB-IX"}
            )

# Run: locust -f tests/performance/test_load.py
# Target: 100 concurrent users, <500ms response time