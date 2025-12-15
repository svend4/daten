"""
Locust Load Testing Suite для IOS System
Stress testing и load testing сценарии
"""
from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import random
import json
from datetime import datetime


class IOSSystemUser(FastHttpUser):
    """
    Базовый пользователь системы IOS
    Симулирует типичное поведение пользователя
    """
    
    # Время ожидания между запросами (1-3 секунды)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Инициализация при старте пользователя"""
        # Авторизация пользователя
        self.login()
        
    def login(self):
        """Авторизация пользователя"""
        response = self.client.post("/api/auth/login", json={
            "username": f"user_{random.randint(1, 1000)}",
            "password": "testpassword123"
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(10)
    def view_dashboard(self):
        """Просмотр dashboard - самая частая операция"""
        self.client.get(
            "/api/dashboard",
            headers=self.headers,
            name="/api/dashboard"
        )
    
    @task(8)
    def search_documents(self):
        """Поиск документов"""
        search_queries = [
            "report", "analysis", "data", "meeting", 
            "presentation", "proposal", "invoice", "contract"
        ]
        query = random.choice(search_queries)
        
        self.client.get(
            f"/api/search?q={query}&limit=20",
            headers=self.headers,
            name="/api/search"
        )
    
    @task(5)
    def view_document(self):
        """Просмотр документа"""
        doc_id = f"doc_{random.randint(1, 10000)}"
        
        self.client.get(
            f"/api/documents/{doc_id}",
            headers=self.headers,
            name="/api/documents/[id]"
        )
    
    @task(3)
    def create_document(self):
        """Создание документа"""
        document = {
            "title": f"Test Document {datetime.now().isoformat()}",
            "content": "This is a test document content " * 50,
            "tags": ["test", "load-testing"],
            "category": random.choice(["report", "memo", "note"])
        }
        
        self.client.post(
            "/api/documents",
            json=document,
            headers=self.headers,
            name="/api/documents"
        )
    
    @task(2)
    def update_document(self):
        """Обновление документа"""
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        update_data = {
            "title": f"Updated Document {datetime.now().isoformat()}",
            "content": "Updated content " * 30
        }
        
        self.client.patch(
            f"/api/documents/{doc_id}",
            json=update_data,
            headers=self.headers,
            name="/api/documents/[id]"
        )
    
    @task(1)
    def delete_document(self):
        """Удаление документа"""
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        self.client.delete(
            f"/api/documents/{doc_id}",
            headers=self.headers,
            name="/api/documents/[id]"
        )
    
    @task(4)
    def semantic_search(self):
        """Семантический поиск"""
        queries = [
            "financial reports from last quarter",
            "meeting notes about project planning",
            "customer feedback and reviews",
            "technical documentation for API"
        ]
        query = random.choice(queries)
        
        self.client.post(
            "/api/search/semantic",
            json={"query": query, "limit": 10},
            headers=self.headers,
            name="/api/search/semantic"
        )
    
    @task(2)
    def knowledge_graph_query(self):
        """Запрос к графу знаний"""
        entity_id = f"entity_{random.randint(1, 500)}"
        
        self.client.get(
            f"/api/graph/entity/{entity_id}/relations",
            headers=self.headers,
            name="/api/graph/entity/[id]/relations"
        )
    
    @task(1)
    def ai_summarization(self):
        """AI суммаризация документа"""
        doc_id = f"doc_{random.randint(1, 1000)}"
        
        self.client.post(
            f"/api/ai/summarize/{doc_id}",
            headers=self.headers,
            name="/api/ai/summarize/[id]"
        )


class HeavyUser(FastHttpUser):
    """
    "Тяжелый" пользователь - делает много операций
    Для stress testing
    """
    
    wait_time = between(0.5, 1.5)  # Более агрессивное поведение
    
    def on_start(self):
        self.login()
        
    def login(self):
        response = self.client.post("/api/auth/login", json={
            "username": f"heavy_user_{random.randint(1, 100)}",
            "password": "testpassword123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task
    def bulk_operations(self):
        """Массовые операции"""
        # Создаем несколько документов подряд
        for i in range(5):
            self.client.post(
                "/api/documents",
                json={
                    "title": f"Bulk Document {i}",
                    "content": "Content " * 100
                },
                headers=self.headers
            )
        
        # Затем делаем поиск
        self.client.get(
            "/api/search?q=bulk&limit=50",
            headers=self.headers
        )


class ReadOnlyUser(FastHttpUser):
    """
    Read-only пользователь - только чтение
    Симулирует пользователей, которые только просматривают
    """
    
    wait_time = between(2, 5)
    
    def on_start(self):
        self.login()
        
    def login(self):
        response = self.client.post("/api/auth/login", json={
            "username": f"readonly_user_{random.randint(1, 500)}",
            "password": "testpassword123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token", "")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.headers = {}
    
    @task(5)
    def browse_documents(self):
        """Просмотр списка документов"""
        page = random.randint(1, 10)
        self.client.get(
            f"/api/documents?page={page}&limit=20",
            headers=self.headers,
            name="/api/documents"
        )
    
    @task(3)
    def view_document_details(self):
        """Просмотр деталей документа"""
        doc_id = f"doc_{random.randint(1, 10000)}"
        self.client.get(
            f"/api/documents/{doc_id}",
            headers=self.headers,
            name="/api/documents/[id]"
        )
    
    @task(2)
    def search(self):
        """Поиск"""
        self.client.get(
            f"/api/search?q={random.choice(['report', 'data', 'meeting'])}",
            headers=self.headers,
            name="/api/search"
        )


class APIUser(FastHttpUser):
    """
    API пользователь - делает прямые API запросы
    Симулирует внешние интеграции
    """
    
    wait_time = between(0.1, 0.5)  # Быстрые запросы
    
    def on_start(self):
        self.api_key = "test_api_key_12345"
        self.headers = {"X-API-Key": self.api_key}
    
    @task
    def api_batch_request(self):
        """Батч запрос через API"""
        self.client.post(
            "/api/v1/batch",
            json={
                "operations": [
                    {"method": "GET", "path": "/documents"},
                    {"method": "GET", "path": "/search?q=test"},
                    {"method": "POST", "path": "/documents", "data": {"title": "API Doc"}}
                ]
            },
            headers=self.headers,
            name="/api/v1/batch"
        )


# Event listeners для статистики
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """При старте теста"""
    print("=" * 60)
    print("🚀 LOAD TEST STARTED")
    print(f"Target Host: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """При остановке теста"""
    print("=" * 60)
    print("🏁 LOAD TEST COMPLETED")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Обработка каждого запроса для детальной статистики"""
    if exception:
        print(f"❌ Request failed: {name} - {exception}")


# Конфигурации для различных сценариев тестирования

class StressTestScenario:
    """Сценарий стресс-тестирования"""
    users = [HeavyUser]
    spawn_rate = 10  # 10 пользователей в секунду
    run_time = "10m"  # 10 минут


class NormalLoadScenario:
    """Сценарий нормальной нагрузки"""
    users = [IOSSystemUser, ReadOnlyUser]
    spawn_rate = 5
    run_time = "30m"


class SpikeTestScenario:
    """Сценарий пиковой нагрузки"""
    users = [IOSSystemUser, HeavyUser, ReadOnlyUser]
    spawn_rate = 20
    run_time = "5m"


class EnduranceTestScenario:
    """Сценарий длительного тестирования"""
    users = [IOSSystemUser, ReadOnlyUser]
    spawn_rate = 2
    run_time = "2h"
